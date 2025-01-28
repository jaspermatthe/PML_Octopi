# coding=utf-8
from __future__ import absolute_import

from datetime import datetime
import os
import requests
import random
import csv
import octoprint.plugin
from octoprint.events import Events
from octoprint.util import RepeatedTimer

__plugin_name__ = "ImageDataCapturerTimedInc"
__plugin_version__ = "1.1.0"
__plugin_description__ = "A plugin to capture an image upon printer connection and log temperature details."
__plugin_pythoncompat__ = ">=3.7,<4" 

class ImageDataCapturerTimedInc(octoprint.plugin.EventHandlerPlugin):

    def on_after_startup(self):
        self._logger.info("ImageDataCapturerTimedInc Plugin started!")
        self._timer = None
        self._total_image_count = 0
        self._batch_image_count = 0
        self.current_parameters = None
        
    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            self._logger.info("Printer connected. Waiting for print to start...")
            # Reset parameters and counters if necessary
            self.current_parameters = {
                'lateral_speed': 100
            }
            self._image_count = 0
            self._total_image_count = 0  # Reset the image counters on each connection
            self._batch_image_count = 0
            self._capture_freq = 0.4 # s

        elif event == Events.PRINT_STARTED:
            self._logger.info("Print has started! Beginning image capture sequence.")
            self.start_timer(self._capture_freq)  # Start the timer to repeat every 1 s (2.5 Hz)
            
        status = payload.get("state_id")
        self._logger.info(f"CURRENT PRINTER STATUS IS: {status}")

    def start_timer(self, interval):
        self._timer = RepeatedTimer(interval, self.snapshot_sequence)
        self._timer.start()

    def snapshot_sequence(self):
        # Check heating status before capturing an image
        if self.check_heating_status():
            self._logger.info("Printer is currently heating/cooling. Skipping image capture.")
            return  # Skip capturing images if the printer is heating/cooling

        if self._batch_image_count >= 150:
            self.resample_and_send_parameters()  # Resample first to send new target temperature with wait to "pause" print
            self._logger.info(f"Captured 150 images (total {self._total_image_count} images); stopping timer and resampling parameters.")
            self._timer.cancel()  # Stop the timer once 150 images are captured
            self._batch_image_count = 0
            self.start_timer(self._capture_freq)  # restart timer and take another batch of images
            return

        # Step 1: Capture the temperatures
        temps = self.capture_temperatures()

        # Step 2: Only if temperatures are successfully captured, proceed to capture the image
        if temps:
            image_name = f"image-{self._total_image_count}.jpg"
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
                    "lateral_speed": self.current_parameters['lateral_speed'],
                }
                self.log_snapshot(snapshot_data)
                self._total_image_count += 1
                self._batch_image_count += 1
                # self._logger.info(f"read lateral speed: {self.current_parameters['lateral_speed']}")

    def check_heating_status(self, threshold=2.5):
        """
        Check if the printer is currently heating or cooling by comparing the actual and target temperatures.
        If the temperature difference exceeds the threshold, it indicates that the printer is heating or cooling.
        """
        temps = self._printer.get_current_temperatures()
        if not temps:
            self._logger.warning("Failed to retrieve temperature data from OctoPrint.")
            return False  # Default to not heating if temperatures are not available
        
        # Get actual and target temperatures for hotend and bed
        hotend_actual = temps['tool0']['actual']
        hotend_target = temps['tool0']['target']
        bed_actual = temps['bed']['actual']
        bed_target = temps['bed']['target']

        # Check if the printer is still heating or cooling (difference greater than threshold)
        hotend_diff = abs(hotend_actual - hotend_target)
        bed_diff = abs(bed_actual - bed_target)

        # If either the hotend or bed is heating or cooling, return True
        if hotend_diff > threshold:
            return True  # Heating or cooling is ongoing
        
        return False  # No heating or cooling

    def resample_and_send_parameters(self):
        try:
            # Resample each parameter from specified ranges
            self.current_parameters['hotend_temp'] = random.uniform(180, 230)
            self.current_parameters['lateral_speed'] = random.uniform(20, 200)
            self.current_parameters['flow_rate'] = random.uniform(20, 200)
            self.current_parameters['z_offset'] = random.uniform(-0.08, 0.32)

            # self._printer.commands(f"M220 S{self.current_parameters['lateral_speed']}")
            # self._logger.info(f"Lateral speed percentage set to: {self.current_parameters['lateral_speed']}%.")

            # send M221 flow rate (e) command AFTER M220 command to override e-component of M220 command
            self._printer.commands(f"M221 S{self.current_parameters['flow_rate']}")
            self._logger.info(f"Flow rate percentage set to: {self.current_parameters['flow_rate']}%.")

            # # Send new Z offset using babystepping
            # self._printer.commands(f"M290 Z{self.current_parameters['z_offset']}")
            # self._logger.info(f"Z offset (babystepping) set to: {self.current_parameters['z_offset']} mm.")

            # Send the new printing parameter commands to the printer
            self._printer.commands(f"M109 R{self.current_parameters['hotend_temp']}")
            self._logger.info("testing mid-print cooldown")
            
        except Exception as e:
            self._logger.error(f"Error setting new parameters: {e}")

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
            # self._logger.info("Image captured successfully.")

            # Save the image to the SD card
            with open(save_path, "wb") as f:
                f.write(response.content)
            # self._logger.info(f"Snapshot saved to {save_path}")
            
            return save_path  # Return the path where the image was saved
        except (requests.RequestException, IOError) as e:
            self._logger.error(f"Error capturing or saving snapshot: {e}")
            return None

    def log_snapshot(self, snapshot_data):
        log_file = "/media/sdcard/snapshots/print_log_full_inc.csv"
        log_exists = os.path.exists(log_file)

        try:
            # Open the CSV file in append mode
            with open(log_file, mode="a", newline="") as file:
                writer = csv.writer(file)
                if not log_exists:
                    # If the log file doesn't exist, write the header first
                    writer.writerow(["Timestamp", "Image Name", "Image Path", "Target Hotend", "Hotend", "Target Bed", "Bed", "Lateral Speed"])
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
                    snapshot_data['lateral_speed']
                ])
                # self._logger.info(f"Logged: {snapshot_data['timestamp']}, {snapshot_data['image_name']}, {snapshot_data['hotend']}, {snapshot_data['lateral_speed']}")
        except IOError as e:
            self._logger.error(f"Error logging snapshot to {log_file}: {e}")

__plugin_implementation__ = ImageDataCapturerTimedInc()
