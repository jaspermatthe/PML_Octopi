import os
import subprocess
import random
import csv
import requests
from datetime import datetime
import octoprint.plugin
from octoprint.events import Events
from octoprint.util import RepeatedTimer
from octoprint.filemanager import FileDestinations

__plugin_name__ = "PmlOctoPrinterFiveConfig"
__plugin_version__ = "1.0.0"
__plugin_description__ = "5 parameter plugin to send G-code files for printing and capture images during the print."
__plugin_pythoncompat__ = ">=3.7,<4"

class PmlOctoPrinterFiveConfig(octoprint.plugin.StartupPlugin, octoprint.plugin.EventHandlerPlugin):

    def on_after_startup(self):
        # This method is called when OctoPrint starts up
        self._logger.info("PmlOctoPrinterFiveConfig started!")
        self._set_camera_focus()
        self._timer = None
        self._image_per_batch = 100  # Number of images per batch
        self._image_count = 0
        self._batch_count = 0
        self.current_parameters = {
            'flow_rate': 100,  # Default flow rate
            'lateral_speed': 100,  # Default lateral speed
            'z_offset': 0.0,  # Default z-offset
            'hotend_temp': 240,  # Default hotend temperature PETG
            'bed_temp': 85  # Default bed temperature PETG
        }
        self._heating_up = False  # Track if the printer is heating up
        self._initial_heatup_complete = False  # Track if initial heatup is complete
        self._parameter_to_sample = None  # Track which parameter is being sampled
        self._default_parameters = self.current_parameters.copy()  # Store default parameters

        # Create the print0 directory if it doesn't exist
        self._print0_dir = "/media/sdcard/snapshots/print0"
        if not os.path.exists(self._print0_dir):
            os.makedirs(self._print0_dir)
            self._logger.info(f"Created directory: {self._print0_dir}")

    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            self._logger.info("Printer connected event detected")
            self._set_camera_focus()
            filename = "3D_benchy.gcode"  # File name in OctoPrint's local storage
            self.send_gcode_file(filename)

        elif event == Events.PRINT_STARTED:
            self._logger.info("Print started event detected")
            self._set_camera_focus()
            self._heating_up = True  # Printer is heating up
            self._initial_heatup_complete = False  # Reset initial heatup flag
            self._image_count = 0  # Reset the image counter on each print start
            self._batch_count = 0  # Reset the batch counter
            self._parameter_to_sample = None  # Reset parameter to sample
            self._set_bed_temperature()  # Set bed temperature to 60°C
            self.start_timer(0.4)  # Start the timer to repeat every 0.4 s (2.5 Hz)

        elif event == Events.PRINT_DONE or event == Events.PRINT_FAILED:
            self._logger.info("Print finished or failed, stopping image capture")
            if self._timer:
                self._timer.cancel()

    def _set_camera_focus(self):
        # Disable autofocus
        try:
            subprocess.run(["v4l2-ctl", "-d", "/dev/video0", "-c", "focus_automatic_continuous=0"], check=True)
            self._logger.info("Autofocus disabled successfully.")
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Failed to disable autofocus: {e}")

        # Set manual focus value
        try:
            subprocess.run(["v4l2-ctl", "-d", "/dev/video0", "-c", "focus_absolute=400"], check=True)
            self._logger.info("Manual focus set to 400 successfully.")
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Failed to set manual focus: {e}")

    def _set_bed_temperature(self):
        # Set bed temperature to 60°C
        self._printer.commands(f"M140 S{self.current_parameters['bed_temp']}")  # Set bed temperature
        self._logger.info(f"Bed temperature set to {self.current_parameters['bed_temp']}°C.")

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
                self._capture_initial_batch(temps)  # Capture initial batch with default parameters
                return  # Skip further processing until the next timer tick

        # Step 2: If initial heatup is complete, proceed with normal image capture
        if self._initial_heatup_complete:
            if self._image_count >= self._image_per_batch:
                # self._image_count = 0  # Reset image counter for new batch
                self._batch_count += 1
                self._sample_next_parameter()  # Sample the next parameter

            # Step 3: Capture the temperatures
            temps = self.capture_temperatures()

            # Step 4: Only if temperatures are successfully captured and nozzle is at target temp, proceed to capture the image
            if temps and self._is_nozzle_at_target_temp(temps):
                image_name = f"image-{self._image_count}.jpg"
                image_path = os.path.join(self._print0_dir, image_name)
                image_path = self.capture_image(image_name, image_path)

                if image_path:
                    # Bundle data into a dictionary and pass to log_snapshot
                    snapshot_data = {
                        "img_path": image_path,
                        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),  # ISO 8601 timestamp
                        "flow_rate": self.current_parameters.get('flow_rate'),
                        "feed_rate": self.current_parameters.get('lateral_speed'),  # Feed rate = lateral speed
                        "z_offset": self.current_parameters.get('z_offset'),
                        "target_hotend": temps['target_hotend'],
                        "hotend": temps['hotend'],
                        "bed": temps['bed'],
                        "nozzle_tip_x": 0,  # Placeholder for nozzle tip X position
                        "nozzle_tip_y": 0,  # Placeholder for nozzle tip Y position
                        "img_num": self._image_count,
                        "print_id": 0  # Single print, so print_id is always 0
                    }
                    self.log_snapshot(snapshot_data)
                    self._image_count += 1
            else:
                self._logger.info("Nozzle temperature not at target, skipping image capture.")

    def _is_heating_complete(self, temps):
        # Check if both hotend and bed have reached their target temperatures
        hotend_reached = abs(temps['hotend'] - temps['target_hotend']) < 1.0  # Tolerance of 1°C
        bed_reached = abs(temps['bed'] - temps['target_bed']) < 1.0  # Tolerance of 1°C
        return hotend_reached and bed_reached

    def _is_nozzle_at_target_temp(self, temps):
        # Check if the nozzle temperature is within ±1°C of the target temperature
        return abs(temps['hotend'] - temps['target_hotend']) <= 1.0

    def _capture_initial_batch(self, temps):
        # Capture 100 images with default parameters
        self._logger.info("Capturing initial batch of 100 images with default parameters")
        for i in range(self._image_per_batch):
            # Check if nozzle is at target temperature before capturing each image
            if self._is_nozzle_at_target_temp(temps):
                image_name = f"image-{i}.jpg"
                image_path = os.path.join(self._print0_dir, image_name)
                image_path = self.capture_image(image_name, image_path)

                if image_path:
                    # Bundle data into a dictionary and pass to log_snapshot
                    snapshot_data = {
                        "img_path": image_path,
                        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),  # ISO 8601 timestamp
                        "flow_rate": self.current_parameters.get('flow_rate'),
                        "feed_rate": self.current_parameters.get('lateral_speed'),  # Feed rate = lateral speed
                        "z_offset": self.current_parameters.get('z_offset'),
                        "target_hotend": temps['target_hotend'],
                        "hotend": temps['hotend'],
                        "bed": temps['bed'],
                        "nozzle_tip_x": 0,  # Placeholder for nozzle tip X position
                        "nozzle_tip_y": 0,  # Placeholder for nozzle tip Y position
                        "img_num": i,
                        "print_id": 0  # Single print, so print_id is always 0
                    }
                    self.log_snapshot(snapshot_data)
            else:
                self._logger.info("Nozzle temperature not at target, skipping image capture.")
        self._logger.info("Initial batch of 100 images captured")

    def _sample_next_parameter(self):
        # Randomly sample one parameter at a time
        parameters_to_sample = ['flow_rate', 'lateral_speed', 'z_offset', 'hotend_temp']
        if self._parameter_to_sample is None:
            # Start sampling the first parameter
            self._parameter_to_sample = random.choice(parameters_to_sample)
        else:
            # Reset the previously sampled parameter to its default value
            self.current_parameters[self._parameter_to_sample] = self._default_parameters[self._parameter_to_sample]
            # Move to the next parameter
            remaining_parameters = [p for p in parameters_to_sample if p != self._parameter_to_sample]
            if remaining_parameters:
                self._parameter_to_sample = random.choice(remaining_parameters)
            else:
                # All parameters have been sampled
                self._parameter_to_sample = None
                return

        # Sample the new parameter
        if self._parameter_to_sample == 'flow_rate':
            self.current_parameters['flow_rate'] = random.uniform(20, 200)
        elif self._parameter_to_sample == 'lateral_speed':
            self.current_parameters['lateral_speed'] = random.uniform(20, 200)
        elif self._parameter_to_sample == 'z_offset':
            self.current_parameters['z_offset'] = random.uniform(-0.08, 0.32)
        elif self._parameter_to_sample == 'hotend_temp':
            self.current_parameters['hotend_temp'] = random.uniform(180, 230)

        # Send the new parameter to the printer
        self._send_parameters_to_printer()

    def _send_parameters_to_printer(self):
        # Send the current parameters to the printer
        self._printer.commands(f"M109 S{self.current_parameters['hotend_temp']}")  # Set hotend temperature
        self._printer.commands(f"M220 S{self.current_parameters['lateral_speed']}")  # Set lateral speed
        self._printer.commands(f"M221 S{self.current_parameters['flow_rate']}")  # Set flow rate
        self._printer.commands(f"M290 Z{self.current_parameters['z_offset']}")  # Set z-offset

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

    def capture_image(self, image_name, image_path):
        webcam_url = "http://10.18.2.98/webcam/?action=snapshot"  # Webcam snapshot URL

        try:
            response = requests.get(webcam_url)
            response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
            self._logger.info("Image captured successfully.")

            # Save the image to the specified path
            with open(image_path, "wb") as f:
                f.write(response.content)
            self._logger.info(f"Snapshot saved to {image_path}")

            return image_path  # Return the path where the image was saved
        except (requests.RequestException, IOError) as e:
            self._logger.error(f"Error capturing or saving snapshot: {e}")
            return None

    def log_snapshot(self, snapshot_data):
        log_file = "/media/sdcard/snapshots/print0/print_log_full.csv"
        log_exists = os.path.exists(log_file)

        try:
            # Open the CSV file in append mode
            with open(log_file, mode="a", newline="") as file:
                writer = csv.writer(file)
                if not log_exists:
                    # If the log file doesn't exist, write the header first
                    writer.writerow([
                        "img_path", "timestamp", "flow_rate", "feed_rate", "z_offset",
                        "target_hotend", "hotend", "bed", "nozzle_tip_x", "nozzle_tip_y",
                        "img_num", "print_id"
                    ])
                    self._logger.info("Created new log file with headers.")

                # Log the data from the dictionary
                writer.writerow([
                    snapshot_data['img_path'],
                    snapshot_data['timestamp'],
                    snapshot_data['flow_rate'],
                    snapshot_data['feed_rate'],
                    snapshot_data['z_offset'],
                    snapshot_data['target_hotend'],
                    snapshot_data['hotend'],
                    snapshot_data['bed'],
                    snapshot_data['nozzle_tip_x'],
                    snapshot_data['nozzle_tip_y'],
                    snapshot_data['img_num'],
                    snapshot_data['print_id']
                ])
                self._logger.info(f"Logged: {snapshot_data['timestamp']}, {snapshot_data['img_path']}")
        except IOError as e:
            self._logger.error(f"Error logging snapshot to {log_file}: {e}")

__plugin_implementation__ = PmlOctoPrinterFiveConfig()