import shutil
import os

# Define source and destination paths
source_path = "/home/raspberry/STL_GCODE/3D_benchy.gcode"  # Include the .gcode extension
destination_path = "/home/raspberry/.octoprint/uploads/3D_benchy.gcode"

try:
    # Check if the file already exists at the destination
    if os.path.exists(destination_path):
        os.remove(destination_path)  # Delete existing file before copying

    # Copy the file (instead of moving)
    shutil.copy2(source_path, destination_path)  # copy2 preserves metadata
    print(f"File copied successfully to {destination_path}")

except FileNotFoundError:
    print(f"Source file not found: {source_path}")
except PermissionError:
    print(f"Permission denied. Check file permissions.")
except Exception as e:
    print(f"An error occurred: {e}")
