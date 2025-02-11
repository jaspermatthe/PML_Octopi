import shutil
import os

# Define source and destination paths
source_path = "/home/raspberry/STL_GCODE/Cute_Mini_Octopus.gcode"
destination_path = "/home/raspberry/.octoprint/uploads/Cute_Mini_Octopus.gcode"

# Move the file
try:
    shutil.move(source_path, destination_path)
    print(f"File moved successfully to {destination_path}")
except FileNotFoundError:
    print(f"Source file not found: {source_path}")
except PermissionError:
    print(f"Permission denied. Check file permissions.")
except Exception as e:
    print(f"An error occurred: {e}")