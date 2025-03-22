#!/usr/bin/env python3
"""
MasterpieceX + BlenderLLM Integration
------------------------------------
This script integrates MasterpieceX's 3D model generation with BlenderLLM's rendering capabilities.
1. Generate a 3D model using MasterpieceX API
2. Automatically render it with Blender
"""

import os
import sys
import time
import argparse
import logging
import tempfile
import shutil
import zipfile
import requests
import platform
import subprocess
from pathlib import Path
from mpx_genai_sdk import Masterpiecex
from scripts.geometry_utils import calculate_bounding_box
from scripts.blender_runner import run_blender_script
from scripts.config import CAMERA_ANGLES, BRIGHTNESS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MPX-BlenderLLM")

def get_default_blender_path():
    """Get the default Blender executable path based on the operating system"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # Common macOS Blender installation paths
        mac_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender/Blender.app/Contents/MacOS/Blender",
        ]
        for path in mac_paths:
            if os.path.exists(path):
                logger.info(f"Found Blender at: {path}")
                return path
        
        logger.warning("Could not find Blender in standard macOS locations")
    
    # Default to command name for Linux/Windows or if macOS paths not found
    return "blender"

def parse_arguments():
    default_blender = get_default_blender_path()
    
    parser = argparse.ArgumentParser(description="MasterpieceX + BlenderLLM Integration")
    parser.add_argument("--prompt", type=str, required=True,
                      help="Text prompt describing what to create")
    parser.add_argument("--output_folder", type=str, default="output",
                      help="Folder to save outputs")
    parser.add_argument("--obj_name", type=str, default=None,
                      help="Name for the output object file (defaults to auto-generated from prompt)")
    parser.add_argument("--poll_interval", type=int, default=10,
                      help="Time in seconds between status checks")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    parser.add_argument("--max_wait", type=int, default=600,
                      help="Maximum time to wait for generation in seconds (default: 10 minutes)")
    parser.add_argument("--blender_executable", type=str, default=default_blender,
                      help=f"Path to Blender executable (default: {default_blender})")
    parser.add_argument("--brightness", type=str, default="Medium Bright", 
                      choices=BRIGHTNESS.keys(), 
                      help="Brightness level for rendering")
    parser.add_argument("--skip_render", action="store_true",
                      help="Skip rendering and only download the model")
    parser.add_argument("--simulate", action="store_true",
                      help="Simulate API calls for testing (no actual API calls)")
    return parser.parse_args()

def get_obj_name_from_prompt(prompt):
    """Generate a filename-safe name from the prompt"""
    words = prompt.split()[:3]  # Take first 3 words
    name = "_".join(words).lower()
    safe_name = "".join(c for c in name if c.isalnum() or c == "_")
    return safe_name or "mpx_model"

def ensure_output_folder(folder_path):
    """Create output folder if it doesn't exist"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.info(f"Created output folder: {folder_path}")
    return folder_path

def download_and_extract_model(download_url, output_folder):
    """Download and extract the model from the provided URL"""
    try:
        # Create a temporary file to download the zip
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            logger.info(f"Downloading model to {temp_file.name}...")
            
            # Download the file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            # Write the content to the temporary file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            temp_file_path = temp_file.name
        
        logger.info(f"Download complete. Extracting...")
        
        # Extract the zip file
        with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        # Find the extracted OBJ file
        obj_files = list(Path(output_folder).glob("**/*.obj"))
        if obj_files:
            logger.info(f"Model extracted successfully. Found {len(obj_files)} OBJ files:")
            for obj_file in obj_files:
                logger.info(f"  - {obj_file}")
            return str(obj_files[0])  # Return the first OBJ file as string path
        else:
            logger.warning("No OBJ files found in the extracted content.")
            return None
    
    except Exception as e:
        logger.error(f"Error downloading or extracting model: {str(e)}")
        return None

def create_simple_script(obj_file):
    """Create a simple Blender script that just imports the OBJ file"""
    obj_path = os.path.abspath(obj_file)
    return f"""import bpy
import os

# Clear any existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import the OBJ file
obj_path = r"{obj_path}"
bpy.ops.import_scene.obj(filepath=obj_path)

# Center the object
for obj in bpy.context.selected_objects:
    bpy.context.view_layer.objects.active = obj
    
# Add a simple material
mat = bpy.data.materials.new(name="MPX_Material")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs[0].default_value = (0.8, 0.8, 0.8, 1.0)  # Base color (light gray)

# Apply material to all objects
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)

# Set basic scene properties
scene = bpy.context.scene
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

# Set up simple lighting
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
"""

def render_model(obj_file, output_folder, obj_name, blender_executable, brightness):
    """Render the model using Blender"""
    try:
        # Create a simple script to import the OBJ
        script = create_simple_script(obj_file)
        
        # Calculate bounding box
        logger.info("Calculating bounding box for camera setup...")
        bounding_coords = calculate_bounding_box(obj_file)
        
        # Render images from multiple angles
        logger.info("Rendering images of the model...")
        brightness_value = BRIGHTNESS.get(brightness, BRIGHTNESS["Medium Bright"])
        
        run_blender_script(
            script,
            obj_name,
            output_folder,
            bounding_coords,
            CAMERA_ANGLES,
            brightness_value,
            blender_executable,
            save_image=True
        )
        
        logger.info(f"✅ Images rendered and saved to {output_folder}")
        return True
    
    except Exception as e:
        logger.error(f"Error rendering model: {str(e)}")
        if logger.level == logging.DEBUG:
            import traceback
            traceback.print_exc()
        return False

def simulation_download_cube_obj(output_folder):
    """Create a simple OBJ file for a cube for simulation mode"""
    obj_content = """# Simple cube OBJ file for simulation
v -1.000000 -1.000000 1.000000
v -1.000000 1.000000 1.000000
v -1.000000 -1.000000 -1.000000
v -1.000000 1.000000 -1.000000
v 1.000000 -1.000000 1.000000
v 1.000000 1.000000 1.000000
v 1.000000 -1.000000 -1.000000
v 1.000000 1.000000 -1.000000
vn -1.0000 0.0000 0.0000
vn 0.0000 0.0000 -1.0000
vn 1.0000 0.0000 0.0000
vn 0.0000 0.0000 1.0000
vn 0.0000 -1.0000 0.0000
vn 0.0000 1.0000 0.0000
f 1//1 2//1 4//1 3//1
f 3//2 4//2 8//2 7//2
f 7//3 8//3 6//3 5//3
f 5//4 6//4 2//4 1//4
f 3//5 7//5 5//5 1//5
f 8//6 4//6 2//6 6//6
"""
    output_path = os.path.join(output_folder, "simulation_cube.obj")
    with open(output_path, 'w') as f:
        f.write(obj_content)
    
    logger.info(f"Created simulation cube OBJ at: {output_path}")
    return output_path

def main():
    args = parse_arguments()
    
    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("BlenderLLM").setLevel(logging.DEBUG)
    
    # Check if in simulation mode
    if args.simulate:
        logger.info("Running in simulation mode - no API calls will be made")
    else:
        # Check if API key is set
        api_key = os.environ.get("MPX_API_KEY")
        if not api_key:
            logger.error("MPX_API_KEY environment variable is not set. Please set it with your MasterpieceX API key.")
            sys.exit(1)
        
        # Set bearer token environment variable expected by the SDK
        os.environ["MPX_SDK_BEARER_TOKEN"] = api_key
    
    # Generate model name from prompt if not provided
    model_name = args.obj_name or get_obj_name_from_prompt(args.prompt)
    
    # Create specific output folder for this model
    output_folder = os.path.join(args.output_folder, model_name)
    ensure_output_folder(output_folder)
    
    if args.simulate:
        # Use simulation mode instead of real API calls
        logger.info(f"Simulating 3D model generation with prompt: '{args.prompt}'")
        logger.info("Simulation API call successful. Simulating download...")
        time.sleep(2)  # Simulate a short wait
        
        # Create a simulated cube OBJ
        obj_file = simulation_download_cube_obj(output_folder)
        
        if obj_file:
            logger.info(f"✅ Simulation model downloaded and extracted to {obj_file}")
            
            # Render the model if not skipped
            if not args.skip_render:
                logger.info("Preparing to render the simulation model with Blender...")
                render_success = render_model(
                    obj_file, 
                    output_folder, 
                    model_name, 
                    args.blender_executable, 
                    args.brightness
                )
                
                if render_success:
                    render_status = "✅ Model rendered successfully"
                else:
                    render_status = "❌ Model rendering failed"
            else:
                render_status = "⏩ Rendering skipped as requested"
            
            # Final status
            logger.info(f"\n🎉 Simulation completed for model '{model_name}'")
            logger.info(f"📂 Check the output at: {os.path.abspath(output_folder)}")
            logger.info(f"📱 Model status: ✅ Downloaded and extracted (simulation)")
            logger.info(f"🖼️ Render status: {render_status}")
            return
        else:
            logger.error("Simulation failed to create an OBJ file")
            sys.exit(1)
    
    # Initialize MasterpieceX client
    client = Masterpiecex()
    
    try:
        # Start model generation
        logger.info(f"Starting 3D model generation with prompt: '{args.prompt}'")
        try:
            response = client.functions.create_general(prompt=args.prompt)
            
            request_id = response.request_id
            logger.info(f"Generation started. Request ID: {request_id}")
            logger.info(f"Remaining credits: {response.balance}")
        except Exception as e:
            error_message = str(e)
            if "Insufficient funds" in error_message:
                logger.error("Your MasterpieceX account has insufficient credits. Please add credits to your account.")
                logger.error("Visit: https://www.masterpiecex.com to manage your credits")
            elif "unauthorized" in error_message.lower() or "authentication" in error_message.lower():
                logger.error("Authentication error. Your API key may be invalid or expired.")
                logger.error("Please check your API key and ensure it's valid.")
            else:
                logger.error(f"API error during generation: {error_message}")
            
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
        
        # Poll the status until complete or timeout
        start_time = time.time()
        while True:
            # Check if we've exceeded the max wait time
            elapsed_time = time.time() - start_time
            if elapsed_time > args.max_wait:
                logger.error(f"Generation timed out after {elapsed_time:.1f} seconds")
                sys.exit(1)
            
            # Get status
            status_response = client.status.retrieve(request_id)
            status = status_response.status
            logger.info(f"Current status: {status} (waited {elapsed_time:.1f}s)")
            
            if status == "completed":
                logger.info("Generation completed successfully!")
                break
            elif status == "failed":
                logger.error("Generation failed")
                error_message = getattr(status_response, 'error', 'Unknown error')
                logger.error(f"Error: {error_message}")
                sys.exit(1)
            
            # Wait before next poll
            time.sleep(args.poll_interval)
        
        # Get the download URL
        assets = status_response.output.assets
        if not assets:
            logger.error("No assets found in the response")
            sys.exit(1)
        
        # Find the ZIP file for download
        download_url = None
        for asset in assets:
            if asset.get("display_name", "").endswith(".zip"):
                download_url = asset.get("url")
                break
        
        if not download_url:
            logger.error("No download URL found for the model")
            sys.exit(1)
        
        # Download and extract the model
        obj_file = download_and_extract_model(download_url, output_folder)
        
        if obj_file:
            logger.info(f"✅ Model downloaded and extracted to {obj_file}")
            
            # Render the model if not skipped
            if not args.skip_render:
                logger.info("Preparing to render the model with Blender...")
                render_success = render_model(
                    obj_file, 
                    output_folder, 
                    model_name, 
                    args.blender_executable, 
                    args.brightness
                )
                
                if render_success:
                    render_status = "✅ Model rendered successfully"
                else:
                    render_status = "❌ Model rendering failed"
            else:
                render_status = "⏩ Rendering skipped as requested"
            
            # Final status
            logger.info(f"\n🎉 Process completed for model '{model_name}'")
            logger.info(f"📂 Check the output at: {os.path.abspath(output_folder)}")
            logger.info(f"📱 Model status: ✅ Downloaded and extracted")
            logger.info(f"🖼️ Render status: {render_status}")
        else:
            logger.error("Failed to download or extract the model")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during process: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 