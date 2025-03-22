import logging
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlenderLLM.config")

# Camera angles for rendering (pairs of phi, theta in degrees)
# phi: vertical angle (0 = top, 90 = horizon, 180 = bottom)
# theta: horizontal angle (0 = front, 90 = right, 180 = back, 270 = left)
CAMERA_ANGLES = [
    (45, 0),    # Front top
    (45, 90),   # Right top
    (45, 180),  # Back top
    (45, 270),  # Left top
    (90, 45),   # Front right
    (20, 45),   # High angle view
]

logger.info(f"Configured {len(CAMERA_ANGLES)} camera angles for rendering")

# Brightness levels for rendering (factor applied to world background)
BRIGHTNESS = {
    "Very Bright": 1.5,
    "Bright": 1.0,
    "Medium Bright": 0.7,
    "Dark": 0.4,
    "Very Dark": 0.2,
}

logger.info(f"Configured brightness levels: {', '.join(BRIGHTNESS.keys())}")

# Legacy camera angles in radians (maintained for backward compatibility)
CAMERA_ANGLES_RADIANS = [
    (math.radians(315), math.radians(180), math.radians(135)),
    (math.radians(45), 0, math.radians(315)),
    (math.radians(45), math.radians(135), math.radians(90)),
    (math.radians(270), math.radians(90), math.radians(90)),
    (math.radians(135), math.radians(135), math.radians(90)),
    (math.radians(90), math.radians(90), math.radians(0)),
    (math.radians(0), math.radians(0), math.radians(90)),
    (math.radians(0), math.radians(90), math.radians(0)),
]

# Legacy brightness settings (maintained for backward compatibility)
BRIGHTNESS_RGB = {
    "Very Bright": (
        (125, 100.0, 75, 100.0, 125, 100.0, 75, 100.0),
    ),
    "Bright": (
        (100, 80.0, 65, 95.0, 110, 95.0, 65, 95.0),
    ),
    "Medium Bright": (
        (75, 65.0, 55, 85.0, 90, 85.0, 55, 85.0),
    ),
    "Dark": (
        (50, 50.0, 45, 75.0, 60, 75.0, 45, 75.0),
    ),
    "Very Dark": (
        (25, 35.0, 35, 65.0, 40, 65.0, 35, 65.0),
    ),
}

# Default system prompt template for script generation
DEFAULT_SYSTEM_PROMPT = """
You are an expert in using Blender's Python API (bpy) to create 3D models. 
Based on the following instruction, write a Python script that will generate 
the desired 3D model in Blender.

Your script should:
1. Start with 'import bpy'
2. Clear the default cube and any other objects
3. Create the specified 3D model using Blender's Python API
4. Apply appropriate materials and colors
5. Set up basic lighting

WRAP YOUR SCRIPT WITH <blender-script> AND </blender-script> TAGS.
Do not include any explanations or comments outside these tags.
"""

logger.info("Configuration loaded successfully")