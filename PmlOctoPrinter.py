import os
import random
import csv
import requests
from datetime import datetime
import octoprint.plugin
from octoprint.events import Events
from octoprint.util import RepeatedTimer
from octoprint.filemanager import FileDestinations

__plugin_name__ = "PmlOctoPrinter"
__plugin_version__ = "1.0.0"
__plugin_description__ = "A plugin to send G-code files for printing and capture images during the print."
__plugin_pythoncompat__ = ">=3.7,<4"

class PmlOctoPrinter(octoprint.plugin.StartupPlugin, octoprint.plugin.EventHandlerPlugin):

    def on_after_startup(self):
        # This method is called when OctoPrint starts up
        self._logger.info("PmlOctoPrinter started!")
        self._timer = None
        self._image_per_batch = 150
        self._image_count = 0
        self._batch_count = 0
        self.current_parameters = {}
        self._heating_up = False  # Track if the printer is heating up
        self._initial_heatup_complete = False  # Track if initial heatup is complete

    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            self._logger.info("Printer connected event detected")
            filename = "3D_benchy.gcode"  # File name in OctoPrint's local storage
            self.send_gcode_file(filename)

        elif event == Events.PRINT_STARTED:
            self._logger.info("Print started event detected")
            self._heating_up = True  # Printer is heating up
            self._initial_heatup_complete = False  # Reset initial heatup flag
            self._image_count = 0  # Reset the image counter on each print start
            self._batch_count = 0  # Reset the batch counter
            self.start_timer(0.4)  # Start the timer to repeat every 0.4 s (2.5 Hz)

        elif event == Events.PRINT_DONE or event == Events.PRINT_FAILED:
            self._logger.info("Print finished or failed, stopping image capture")
            if self._timer:
                self._timer.cancel()

    def send_gcode_file(self, filename):
        # Ensure the file is in OctoPrint's local storage
        file_path = self._file_manager.path_on_disk(FileDestinations.LOCAL, filename)
        self._logger.info(f"Sending G-code file: {file_path}")

        # Select and start the print job
        self._printer.select_file(file_path, False)  # False means don't start immediately
        self._printer.start_print()  # Start the print job

    def start_timer(self, interval):
        self._timer = RepeatedTimer(interval, self.snapshot_sequence)
        self._timer.start()

    def snapshot_sequence(self):
        # Step 1: Check if the printer is heating up
        if self._heating_up:
            temps = self.capture_temperatures()
            if temps and self._is_heating_complete(temps):
                self._logger.info("Initial heatup complete, capturing initial batch of images")
                self._heating_up = False
                self._initial_heatup_complete = True
                self._capture_initial_batch(temps)  # Capture initial batch with heatup parameters
                return  # Skip further processing until the next timer tick

        # Step 2: If initial heatup is complete, proceed with normal image capture
        if self._initial_heatup_complete:
            if self._image_count >= self._image_per_batch:
                self._image_count = 0  # Reset image counter for new batch
                self._batch_count += 1
                self.resample_and_send_parameters()  # Resample parameters for new batch

            # Step 3: Capture the temperatures
            temps = self.capture_temperatures()

            # Step 4: Only if temperatures are successfully captured, proceed to capture the image
            if temps:
                image_name = f"batch-{self._batch_count}_image-{self._image_count}.jpg"
                image_path = self.capture_image(image_name)

                if image_path:
                    # Bundle data into a dictionary and pass to log_snapshot
                    snapshot_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # High-precision timestamp
                        "image_name": image_name,
                        "image_path": image_path,
                        "target_hotend": temps['target_hotend'],
                        "hotend": temps['hotend'],
                        "target_bed": temps['target_bed'],
                        "bed": temps['bed'],
                        # Include current parameters for the batch
                        "flow_rate": self.current_parameters.get('flow_rate'),
                        "lateral_speed": self.current_parameters.get('lateral_speed'),
                        "z_offset": self.current_parameters.get('z_offset'),
                        "target_hotend_temp": self.current_parameters.get('hotend_temp')
                    }
                    self.log_snapshot(snapshot_data)
                    self._image_count += 1

    def _is_heating_complete(self, temps):
        # Check if both hotend and bed have reached their target temperatures
        hotend_reached = abs(temps['hotend'] - temps['target_hotend']) < 1.0  # Tolerance of 1°C
        bed_reached = abs(temps['bed'] - temps['target_bed']) < 1.0  # Tolerance of 1°C
        return hotend_reached and bed_reached

    def _capture_initial_batch(self, temps):
        # Capture one batch of images with the initial heatup parameters
        self._logger.info("Capturing initial batch of images with heatup parameters")
        for i in range(self._image_per_batch):
            image_name = f"batch-{self._batch_count}_image-{i}.jpg"
            image_path = self.capture_image(image_name)

            if image_path:
                # Bundle data into a dictionary and pass to log_snapshot
                snapshot_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  # High-precision timestamp
                    "image_name": image_name,
                    "image_path": image_path,
                    "target_hotend": temps['target_hotend'],
                    "hotend": temps['hotend'],
                    "target_bed": temps['target_bed'],
                    "bed": temps['bed'],
                    # Include initial heatup parameters
                    "flow_rate": self.current_parameters.get('flow_rate'),
                    "lateral_speed": self.current_parameters.get('lateral_speed'),
                    "z_offset": self.current_parameters.get('z_offset'),
                    "target_hotend_temp": self.current_parameters.get('hotend_temp')
                }
                self.log_snapshot(snapshot_data)
        self._logger.info("Initial batch of images captured")

    def resample_and_send_parameters(self):
        # Step 4.1: Resample each parameter from specified ranges
        self.current_parameters['flow_rate'] = random.uniform(20, 200)
        self.current_parameters['lateral_speed'] = random.uniform(20, 200)
        self.current_parameters['z_offset'] = random.uniform(-0.08, 0.32)
        self.current_parameters['hotend_temp'] = random.uniform(180, 230)

        # Step 4.2: Send new parameters as G-code commands
        # Send new hotend temperature
        self._printer.commands(f"M109 S{self.current_parameters['hotend_temp']}")
        self._logger.info(f"Hotend temperature set to: {self.current_parameters['hotend_temp']}°C and waiting to stabilize.")

        # Send new lateral speed
        self._printer.commands(f"M220 S{self.current_parameters['lateral_speed']}")
        self._logger.info(f"Lateral speed percentage set to: {self.current_parameters['lateral_speed']}%.")

        # Send new flow rate
        self._printer.commands(f"M221 S{self.current_parameters['flow_rate']}")
        self._logger.info(f"Flow rate percentage set to: {self.current_parameters['flow_rate']}%.")

        # Send new Z offset using babystepping
        self._printer.commands(f"M290 Z{self.current_parameters['z_offset']}")
        self._logger.info(f"Z offset (babystepping) set to: {self.current_parameters['z_offset']} mm.")

    def capture_temperatures(self):
        try:
            temps = self._printer.get_current_temperatures()

            if not temps or 'tool0' not in temps:
                self._logger.warning("No valid temperature data available.")
                return None

            # Return a dictionary with relevant temperature data
            return {
                'target_hotend': temps['tool0']['target'],
                'hotend': temps['tool0']['actual'],
                'target_bed': temps['bed']['target'],
                'bed': temps['bed']['actual']
            }
        except Exception as e:
            self._logger.error(f"Error retrieving temperature data: {e}")
            return None

    def capture_image(self, image_name):
        webcam_url = "http://10.18.2.98/webcam/?action=snapshot"  # Webcam snapshot URL
        save_dir = "/media/sdcard/snapshots"  # Save location directory on SD card
        save_path = os.path.join(save_dir, image_name)  # Full path to save the image

        # Create directory if it doesn't exist
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            self._logger.info(f"Created snapshot directory: {save_dir}")

        try:
            response = requests.get(webcam_url)
            response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
            self._logger.info("Image captured successfully.")

            # Save the image to the SD card
            with open(save_path, "wb") as f:
                f.write(response.content)
            self._logger.info(f"Snapshot saved to {save_path}")

            return save_path  # Return the path where the image was saved
        except (requests.RequestException, IOError) as e:
            self._logger.error(f"Error capturing or saving snapshot: {e}")
            return None

    def log_snapshot(self, snapshot_data):
        log_file = "/media/sdcard/snapshots/print_log_full.csv"
        log_exists = os.path.exists(log_file)

        try:
            # Open the CSV file in append mode
            with open(log_file, mode="a", newline="") as file:
                writer = csv.writer(file)
                if not log_exists:
                    # If the log file doesn't exist, write the header first
                    writer.writerow(["Timestamp", "Image Name", "Image Path", "Target Hotend", "Hotend", "Target Bed", "Bed",
                                     "Flow Rate", "Lateral Speed", "Z Offset", "Target Hotend Temperature"])
                    self._logger.info("Created new log file with headers.")

                # Log the data from the dictionary
                writer.writerow([
                    snapshot_data['timestamp'],
                    snapshot_data['image_name'],
                    snapshot_data['image_path'],
                    snapshot_data['target_hotend'],
                    snapshot_data['hotend'],
                    snapshot_data['target_bed'],
                    snapshot_data['bed'],
                    snapshot_data['flow_rate'],
                    snapshot_data['lateral_speed'],
                    snapshot_data['z_offset'],
                    snapshot_data['target_hotend_temp']
                ])
                self._logger.info(f"Logged: {snapshot_data['timestamp']}, {snapshot_data['image_name']}, {snapshot_data['target_hotend']}, {snapshot_data['hotend']}")
        except IOError as e:
            self._logger.error(f"Error logging snapshot to {log_file}: {e}")

__plugin_implementation__ = PmlOctoPrinter()