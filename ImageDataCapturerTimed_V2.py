# coding=utf-8
from __future__ import absolute_import

from datetime import datetime
import os
import random
import requests
import csv
import octoprint.plugin
from octoprint.events import Events
from octoprint.util import RepeatedTimer

__plugin_name__ = "ImageDataCapturerTimed"
__plugin_version__ = "1.1.0"
__plugin_description__ = "A plugin to capture an image upon printer connection and log temperature details."
__plugin_pythoncompat__ = ">=3.7,<4" 

class ImageDataCapturerTimed(octoprint.plugin.EventHandlerPlugin):

    # Initialize counters, timers, and loggers
    def on_after_startup(self):
        self._logger.info("ImageCapturerTimed Plugin started!")
        self._timer = None              
        self._image_per_batch = 150
        self._image_count = 0           
        self._batch_count = 0           
        self.current_parameters = {}    

    # Monitor printer events to activate random parameter sampling
    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            self._image_count = 0  # Reset the image counter on each connection
            self._batch_count = 0  # Reset the batch counter
            self.resample_and_send_parameters()  # Initial parameter sampling
            self.start_timer(0.4)  # Start the timer to repeat every 0.4 s (2.5 Hz), so that an image is taken every 0.4s
    
    def start_timer(self, interval):
        self._timer = RepeatedTimer(interval, self.snapshot_sequence)
        self._timer.start()

    def snapshot_sequence(self):
        if self._image_count >= self._image_per_batch:
            self._image_count = 0  # Reset image counter for new batch
            self._batch_count += 1
            self.resample_and_send_parameters()  # Resample parameters for new batch
        
        # Step 1: Capture the temperatures
        temps = self.capture_temperatures()

        # Step 2: Only if temperatures are successfully captured, proceed to capture the image
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

__plugin_implementation__ = ImageDataCapturerTimed()
