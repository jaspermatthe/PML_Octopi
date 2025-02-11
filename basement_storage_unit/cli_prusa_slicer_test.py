import subprocess
import os
import random  # Import the random module

# Path to your PrusaSlicer AppImage
prusa_slicer_path = os.path.expanduser("/home/raspberry/Documents/PrusaSlicer-2.7.3+linux-armv7l-GTK2-202403280945.AppImage")
stl_file_path = "/home/raspberry/thingiscrape/downloads/stls/#3DBenchy_-_The_jolly_3D_printing_torture-test_by_CreativeTools.se/3DBenchy.stl"
output_gcode_path = "/home/raspberry/STL_GCODE/3D_benchy.gcode"  # Include the .gcode extension

# Ensure the paths are correct
if not os.path.exists(prusa_slicer_path):
    raise FileNotFoundError(f"PrusaSlicer AppImage not found at {prusa_slicer_path}")
if not os.path.exists(stl_file_path):
    raise FileNotFoundError(f"STL file not found at {stl_file_path}")

# Parameters
rotation = random.randint(0, 360)  # Random rotation
scale = random.uniform(0.8, 2.0)  # Scale between 0.8 and 2.0
solid_layers = (random.randint(2, 4), random.randint(2, 4))  # Random solid layers
infill_patterns = [
    "rectilinear", "grid", "triangles", "stars", "cubic", 
    "line", "concentric", "honeycomb", "3dhoneycomb", 
    "gyroid", "hilbertcurve", "archimedeanchords", "octagramspiral"
]
infill_pattern = random.choice(infill_patterns)  # Random infill pattern
infill_density = random.uniform(0.0, 0.40)  # Infill density between 0 and 40%
perimeters = random.randint(2, 4)  # Perimeters between 2 and 4
bed_temperature = 60  # Bed temperature
hotend_temperature = 200  # Hotend temperature

# Print sampled parameters
print(f"Sampled rotation: {rotation} degrees")  
print(f"Sampled scale: {scale:.2f}")
print(f"Sampled solid layers (top, bottom): {solid_layers}")
print(f"Sampled infill pattern: {infill_pattern}")
print(f"Sampled infill density: {infill_density:.2f}")
print(f"Sampled perimeters: {perimeters}")
print(f"Sampled bed temperature: {bed_temperature}°C")
print(f"Sampled hotend temperature: {hotend_temperature}°C")

# Centering coordinates for MK3/S/+ print volume
center_x = 125  # Half of 250 mm
center_y = 105  # Half of 210 mm

# Custom Start G-code (optimized heating)
start_gcode = f"""
M140 S{bed_temperature}  ; Set bed temp (non-blocking)
M104 S{hotend_temperature}  ; Set hotend temp (non-blocking)
G28  ; Home all axes
G1 Z5 F5000  ; Lift nozzle
M190 S{bed_temperature}  ; Wait for bed temp
M109 S{hotend_temperature}  ; Wait for hotend temp
G21  ; Set units to millimeters
G90  ; Use absolute positioning
M82  ; Use absolute extrusion
G92 E0  ; Reset extruder position
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
