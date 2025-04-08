import subprocess
import os
import random

# Path to your PrusaSlicer AppImage
prusa_slicer_path = os.path.expanduser("/home/raspberry/Documents/PrusaSlicer-2.7.3+linux-armv7l-GTK2-202403280945.AppImage")
stl_file_path = "/home/raspberry/thingiscrape/downloads/stls/wall_thin.stl"
output_gcode_path = "/home/raspberry/STL_GCODE/wall_thin.gcode"  # Include the .gcode extension

# Ensure the paths are correct
if not os.path.exists(prusa_slicer_path):
    raise FileNotFoundError(f"PrusaSlicer AppImage not found at {prusa_slicer_path}")
if not os.path.exists(stl_file_path):
    raise FileNotFoundError(f"STL file not found at {stl_file_path}")

# Prompt user to choose between PLA and PETG
material_choice = input("Choose material (PLA/PETG): ").strip().upper()

# Set temperatures based on user choice
if material_choice == "PETG":
    bed_temperature = 85
    hotend_temperature = 230
elif material_choice == "PLA":
    bed_temperature = 60
    hotend_temperature = 215

# Parameters
# rotation = random.randint(0, 360)  # Random rotation
rotation = 0
# scale = random.uniform(0.8, 2.0)  # Scale between 0.8 and 2.0
scale = 0.7
solid_layers = (random.randint(2, 4), random.randint(2, 4))  # Random solid layers
infill_patterns = [
    "rectilinear", "grid", "triangles", "stars", "cubic", 
    "line", "concentric", "honeycomb", "3dhoneycomb",
    "gyroid", "hilbertcurve", "archimedeanchords", "octagramspiral"
]
infill_pattern = "honeycomb"  # random.choice(infill_patterns)
# infill_density = random.uniform(0.20, 0.40)  # Infill density between 0 and 40%
infill_density = 0.40
perimeters = random.randint(2, 4)  # Perimeters between 2 and 4

# Print sampled parameters
print(f"Sampled rotation: {rotation} degrees")  
print(f"Sampled scale: {scale:.2f}")
print(f"Sampled solid layers (top, bottom): {solid_layers}")
print(f"Sampled infill pattern: {infill_pattern}")
print(f"Sampled infill density: {infill_density:.2f}")
print(f"Sampled perimeters: {perimeters}")
print(f"Bed temperature: {bed_temperature}°C")
print(f"Hotend temperature: {hotend_temperature}°C")

# Centering coordinates for MK3/S/+ print volume
center_x = 125  # Half of 250 mm
center_y = 226  # Half of 210 mm

# Custom Start G-code (optimized heating with purge line)
start_gcode = f"""
G90 ; use absolute coordinates
M83 ; extruder relative mode
M140 S{bed_temperature} ; set bed temp
M104 S{hotend_temperature} ; set hotend temp

G28 ; home all axes
G1 X0 Z0.6 Y-3.0 F1000.0 ; move outside print area for intro line
M109 S{hotend_temperature} ; wait for hotend temp
M190 S{bed_temperature} ; wait for bed temp

G92 E0.0 ; reset extruder position
G1 X60.0 E9.0 F1000.0 ; draw the first line (extrude 9mm)
G1 X100.0 E12.5 F1000.0 ; draw the second line (extrude 3.5mm more)
G92 E0.0 ; reset extruder position
G90 ; use absolute coordinates
M82 ; use absolute extrusion
"""

# Command to run PrusaSlicer
command = [
    prusa_slicer_path,
    "--slice",  # Slice the STL file
    "--scale", str(scale),
    "--rotate", str(rotation),
    "--center", f"{center_x},{center_y}",  # Center the model
    "--top-solid-layers", str(solid_layers[0]),  # Top solid layers
    "--bottom-solid-layers", str(solid_layers[1]),  # Bottom solid layers
    "--fill-pattern", infill_pattern,  # Infill pattern
    "--fill-density", str(infill_density),  # Infill density
    "--perimeters", str(perimeters),  # Perimeters
    "--first-layer-bed-temperature", str(bed_temperature),  # Set bed temp
    "--first-layer-temperature", str(hotend_temperature),  # Set hotend temp
    "--output", output_gcode_path,  # Output G-code file
    "--start-gcode", start_gcode,  # Inject optimized start G-code
    stl_file_path
]

# Run the command
try:
    subprocess.run(command, check=True)
    print(f"Slicing completed! G-code saved to {output_gcode_path}")
except subprocess.CalledProcessError as e:
    print(f"An error occurred while slicing: {e}")