import os
import subprocess
import tempfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlenderLLM.runner")

def create_blender_script(script, obj_name, output_folder, bounding_coords=None, camera_angles=None, brightness=None, save_obj=False, save_image=False):
    """Creates a Python script to be executed in Blender."""
    
    # Create a temporary file to hold the script
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as temp_file:
        # Add setup code to clear any existing objects
        temp_file.write("import bpy\n")
        temp_file.write("# Clear any existing objects\n")
        temp_file.write("bpy.ops.object.select_all(action='SELECT')\n")
        temp_file.write("bpy.ops.object.delete()\n\n")
        
        # Add the user's script
        temp_file.write(script)
        
        if save_obj:
            # If we need to save an OBJ file, add code to do so
            temp_file.write(f"""
# Save OBJ output code
output_path = "{output_folder}/{obj_name}.obj"
print(f"Saving object to: {{output_path}}")
bpy.ops.export_scene.obj(filepath=output_path, use_selection=False)
print("Object saved successfully")
""")
        
        if save_image and bounding_coords and camera_angles:
            # Generate camera setup and rendering code if needed
            camera_setup = generate_camera_setup(obj_name, bounding_coords, camera_angles, brightness, output_folder)
            temp_file.write(camera_setup)
        
        script_path = temp_file.name
    
    logger.info(f"Created temporary Blender script at: {script_path}")
    return script_path

def generate_camera_setup(obj_name, bounding_coords, camera_angles, brightness, output_folder):
    """Generate Blender Python code for camera setup."""
    # Determine if we're using the new format (6-tuple) or legacy format (list of coords)
    if isinstance(bounding_coords, tuple) and len(bounding_coords) == 6:
        # New format: (min_x, min_y, min_z, max_x, max_y, max_z)
        min_x, min_y, min_z, max_x, max_y, max_z = bounding_coords
        
        # Calculate center and dimensions
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        
        # Calculate camera distance based on bounding box size
        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z
        max_dimension = max(size_x, size_y, size_z)
        camera_distance = max_dimension * 3.0  # Adjust this multiplier as needed
        
        logger.info(f"Using bounding box format: center at ({center_x:.2f}, {center_y:.2f}, {center_z:.2f}), distance: {camera_distance:.2f}")
    
    elif isinstance(bounding_coords, list) and len(bounding_coords) > 0:
        # Legacy format: list of camera coordinates
        # For this we'll calculate an approximate center and distance
        coords_x = [c[0] for c in bounding_coords]
        coords_y = [c[1] for c in bounding_coords]
        coords_z = [c[2] for c in bounding_coords]
        
        center_x = sum(coords_x) / len(coords_x)
        center_y = sum(coords_y) / len(coords_y)
        center_z = sum(coords_z) / len(coords_z)
        
        # Calculate approximate distance as average distance from center to points
        distances = [((x - center_x)**2 + (y - center_y)**2 + (z - center_z)**2)**0.5 
                    for x, y, z in bounding_coords]
        camera_distance = sum(distances) / len(distances)
        
        logger.info(f"Using camera coordinates format: center at ({center_x:.2f}, {center_y:.2f}, {center_z:.2f}), distance: {camera_distance:.2f}")
    
    else:
        # Fallback: use default values
        logger.warning("Invalid bounding coordinates, using fallback values")
        center_x, center_y, center_z = 0, 0, 0
        camera_distance = 5.0
    
    # Generate camera setup code
    camera_code = f"""
import math
import os
from mathutils import Vector, Matrix

# First, set world background to a neutral color
if "World" not in bpy.data.worlds:
    bpy.data.worlds.new("World")
    bpy.context.scene.world = bpy.data.worlds["World"]

# Ensure world has nodes
bpy.context.scene.world.use_nodes = True
if "Background" not in bpy.data.worlds["World"].node_tree.nodes:
    # Create new background node if it doesn't exist
    tree = bpy.context.scene.world.node_tree
    background = tree.nodes.new(type="ShaderNodeBackground")
    output = tree.nodes["World Output"] if "World Output" in tree.nodes else tree.nodes.new(type="ShaderNodeOutputWorld")
    tree.links.new(background.outputs[0], output.inputs[0])

# Set background color and brightness
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [1, 1, 1, 1]
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = {brightness}

# Ensure output folder exists
os.makedirs("{output_folder}", exist_ok=True)

# Set render settings
bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024

# Set render engine based on availability
if hasattr(bpy.context.scene, 'cycles'):
    bpy.context.scene.render.engine = 'CYCLES'
    if hasattr(bpy.context.scene.cycles, 'samples'):
        bpy.context.scene.cycles.samples = 64  # Lower for faster renders, increase for quality
else:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'

# Remove any existing cameras
for obj in bpy.data.objects:
    if obj.type == 'CAMERA':
        bpy.data.objects.remove(obj)

# Create camera and generate renders from different angles
center = ({center_x}, {center_y}, {center_z})
distance = {camera_distance}

# Create a function to handle quaternion calculation that works in all Blender versions
def look_at(location, target):
    # Create a direction vector
    direction = Vector((target[0] - location[0], target[1] - location[1], target[2] - location[2])).normalized()
    
    # Get a reference up vector
    up = Vector((0, 0, 1))
    if abs(direction.dot(up)) > 0.999:
        up = Vector((0, 1, 0))
    
    # Create a coordinate system
    z_axis = -direction  # Camera looks down negative z-axis
    x_axis = up.cross(z_axis).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    
    # Create rotation matrix and convert to quaternion
    rot_mat = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
    return rot_mat.to_quaternion()

# Process camera angles
for idx, angle in enumerate({camera_angles}):
    # Extract angle components (phi, theta)
    if len(angle) >= 2:
        phi, theta = angle[0], angle[1]
        
        # Convert spherical coordinates to Cartesian
        phi_rad = math.radians(phi)
        theta_rad = math.radians(theta)
        x = center[0] + distance * math.sin(phi_rad) * math.cos(theta_rad)
        y = center[1] + distance * math.sin(phi_rad) * math.sin(theta_rad)
        z = center[2] + distance * math.cos(phi_rad)
        
        # Create camera
        bpy.ops.object.camera_add(location=(x, y, z))
        camera = bpy.context.active_object
        camera.name = f"Camera_{{idx}}"
        
        # Point camera to center
        camera.rotation_mode = 'QUATERNION'
        camera.rotation_quaternion = look_at((x, y, z), center)
        
        # Set up scene and render
        bpy.context.scene.camera = camera
        
        # Set output path
        angle_name = f"angle_{{idx:02d}}"
        bpy.context.scene.render.filepath = os.path.join("{output_folder}", f"{obj_name}_{{angle_name}}.png")
        
        # Render
        print(f"Rendering image from angle {{idx}}...")
        bpy.ops.render.render(write_still=True)
        print(f"Rendered image saved to {{bpy.context.scene.render.filepath}}")
"""
    return camera_code

def run_blender_script(script, obj_name, output_folder, bounding_coords, camera_angles, brightness, blender_executable, save_obj=False, save_image=False):
    """Run a Blender script using the specified Blender executable."""
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create the Blender script
    script_path = create_blender_script(script, obj_name, output_folder, bounding_coords, camera_angles, brightness, save_obj, save_image)
    
    # Prepare the command to run Blender
    cmd = [blender_executable, '--background', '--python', script_path]
    
    # Log the command
    logger.info(f"Running Blender command: {' '.join(cmd)}")
    
    try:
        # Run Blender as a subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Capture and log the output
        stdout, stderr = process.communicate()
        
        # Log command output
        if stdout:
            logger.info(f"Blender stdout:\n{stdout}")
        if stderr:
            logger.error(f"Blender stderr:\n{stderr}")
        
        if process.returncode != 0:
            logger.error(f"Blender exited with code {process.returncode}")
            if os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    logger.debug(f"Executed script content:\n{f.read()}")
            
            # Since there was an error, let's verify if the output was created
            obj_file_path = os.path.join(output_folder, f"{obj_name}.obj")
            if save_obj and not os.path.exists(obj_file_path):
                logger.error(f"OBJ file was not created at: {obj_file_path}")
            elif save_obj:
                logger.info(f"OBJ file was created despite error: {obj_file_path}")
                # Check if the file has content
                file_size = os.path.getsize(obj_file_path)
                logger.info(f"OBJ file size: {file_size} bytes")
        else:
            logger.info("Blender executed successfully")
    except Exception as e:
        logger.error(f"Error running Blender: {str(e)}")
        raise
    finally:
        # Clean up the temporary script file
        try:
            os.unlink(script_path)
            logger.info(f"Removed temporary script: {script_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary script: {str(e)}")
    
    # Return the path to the generated OBJ file
    return os.path.join(output_folder, f"{obj_name}.obj")
