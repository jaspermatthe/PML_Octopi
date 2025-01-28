import subprocess
import os
import random  # Import the random module

# Path to your PrusaSlicer AppImage
prusa_slicer_path = os.path.expanduser("/home/raspberry/Documents/PrusaSlicer-2.7.3+linux-armv7l-GTK2-202403280945.AppImage")
stl_file_path = "/home/raspberry/thingiscrape/downloads/stls/Cute_Mini_Octopus_/Octopus_v6.stl"
output_gcode_path = "/home/raspberry/STL_GCODE/Cute_Mini_Octopus.gcode"  # Include the .gcode extension

# Ensure the paths are correct
if not os.path.exists(prusa_slicer_path):
    raise FileNotFoundError(f"PrusaSlicer AppImage not found at {prusa_slicer_path}")
if not os.path.exists(stl_file_path):
    raise FileNotFoundError(f"STL file not found at {stl_file_path}")

# Parameters
rotation = random.randint(0, 360)  # Randomly sample rotation between 0 and 360
# Sampled parameters
scale = random.uniform(0.8, 2.0)  # Scale between 0.8 and 2.0
solid_layers = (random.randint(2, 4), random.randint(2, 4))  # Random top and bottom layers between 2 and 4
infill_patterns = [
    "rectilinear", "grid", "triangles", "stars", "cubic", 
    "line", "concentric", "honeycomb", "3dhoneycomb", 
    "gyroid", "hilbertcurve", "archimedeanchords", "octagramspiral"
]
infill_pattern = random.choice(infill_patterns)  # Randomly choose an infill pattern
infill_density = random.uniform(0.0, 0.40)  # Infill density between 0 and 0.40
perimeters = random.randint(2, 4)  # Number of external perimeter walls between 2 and 4

# Print sampled parameters
print(f"Sampled rotation: {rotation} degrees")  # Print the sampled rotation
print(f"Sampled scale: {scale:.2f}")
print(f"Sampled solid layers (top, bottom): {solid_layers}")
print(f"Sampled infill pattern: {infill_pattern}")
print(f"Sampled infill density: {infill_density:.2f}")
print(f"Sampled perimeters: {perimeters}")

# Centering coordinates for MK3/S/+ print volume
center_x = 125  # Half of 250 mm
center_y = 105  # Half of 210 mm

# Command to run PrusaSlicer to slice the STL file
command = [
    prusa_slicer_path,
    # ACTIONS
    "--slice",  # Add slicing command

    # TRANSFORMATIONS
    "--scale", str(scale),
    "--rotate", str(rotation),
    "--center", f"{center_x},{center_y}",  # Center the model

    # MISC OPTIONS
    "--top-solid-layers", str(solid_layers[0]),  # Number of top solid layers
    "--bottom-solid-layers", str(solid_layers[1]),  # Number of bottom solid layers
    "--fill-pattern", infill_pattern,  # Infill pattern
    "--fill-density", str(infill_density),  # Infill density percentage
    "--perimeters", str(perimeters),  # Number of external perimeter walls

    # OUTPUT
    "--output", output_gcode_path,  # Specify the output G-code file

    # STL FILE PATH
    stl_file_path
]

# Run the command
try:
    subprocess.run(command, check=True)
    print(f"Slicing completed! G-code saved to {output_gcode_path}")
except subprocess.CalledProcessError as e:
    print(f"An error occurred while slicing: {e}")
