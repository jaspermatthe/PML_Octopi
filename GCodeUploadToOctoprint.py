import shutil
import os

# Define source and destination paths
source_path = "/home/raspberry/STL_GCODE/3D_benchy.gcode"  # Include the .gcode extension
destination_path = "/home/raspberry/.octoprint/uploads/3D_benchy.gcode"

try:
    # Check if the file already exists at the destination
    if os.path.exists(destination_path):
        os.remove(destination_path)  # Delete existing file before copying

    # Read the source G-code file and replace any S200 with S230
    with open(source_path, 'r') as file:
        gcode_content = file.read()
    
    # Replace S200 with S230
    gcode_content = gcode_content.replace('S200', 'S230')

    # Write the modified content to the destination
    with open(destination_path, 'w') as file:
        file.write(gcode_content)

    print(f"File copied and modified successfully to {destination_path}")

except FileNotFoundError:
    print(f"Source file not found: {source_path}")
except PermissionError:
    print(f"Permission denied. Check file permissions.")
except Exception as e:
    print(f"An error occurred: {e}")
