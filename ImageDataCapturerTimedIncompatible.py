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
        if event == Events.PRINT_STARTED:
            self.current_parameters = {
                'lateral_speed': 100 # start low to see difference
            } # initialize with 100% default
            self._total_image_count = 0  # Reset the image counters on each connection
            self._batch_image_count = 0
            self.start_timer(0.4)  # Start the timer to repeat every 0.4 s (2.5 Hz)
    
    def start_timer(self, interval):
        self._timer = RepeatedTimer(interval, self.snapshot_sequence)
        self._timer.start()

    # def pause_print(self):
    #     try:
    #         self._printer.commands("M25")  # Use M25 to pause the print
    #         self._logger.info("Print paused successfully.")
    #     except Exception as e:
    #         self._logger.error(f"Error pausing the print: {e}")

    # def resume_print(self):
    #     try:
    #         self._printer.commands("M24")  # Send M24 command to resume the print
    #         self._logger.info("Print resumed successfully.")
    #         self._batch_image_count = 0
    #         self.start_timer(0.4)
    #     except Exception as e:
    #         self._logger.error(f"Error resuming the print: {e}")

    def snapshot_sequence(self):
        if self._image_count >= 10:
            # self.pause_print()
            self._logger.info("Captured 10 images; stopping timer and resampling parameters.")
            self._timer.cancel()  # Stop the timer once 10 images are captured
            # self.resample_and_send_parameters()
            self.current_parameters['lateral_speed'] = 200  # test if speed increases
            self.resume_print()
            return

        # Step 1: Capture the temperatures
        temps = self.capture_temperatures()

        # Step 2: Only if temperatures are successfully captured, proceed to capture the image
        if temps:
            image_name = f"image-{self._image_count}.jpg"
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
                self._image_count += 1
                self._logger.info(f"read lateral speed: {self.current_parameters['lateral_speed']}")

    def resample_and_send_parameters(self):
        try:
            # Step 4.1: Resample each parameter from specified ranges
            self.current_parameters['lateral_speed'] = random.uniform(20, 200)

            # Send the new lateral speed command to the printer
            self._printer.commands(f"M220 S{self.current_parameters['lateral_speed']}")
            self._logger.info(f"Lateral speed percentage set to: {self.current_parameters['lateral_speed']}%.")
            
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
                self._logger.info(f"Logged: {snapshot_data['timestamp']}, {snapshot_data['image_name']}, {snapshot_data['hotend']}, {snapshot_data['lateral_speed']}")
        except IOError as e:
            self._logger.error(f"Error logging snapshot to {log_file}: {e}")

__plugin_implementation__ = ImageDataCapturerTimedInc()