#!/usr/bin/env python3
"""
MasterpieceX Direct Downloader
-----------------------------
Download existing 3D models from MasterpieceX using a direct URL.
"""

import os
import sys
import time
import argparse
import logging
import tempfile
import shutil
import zipfile
import json
import requests
import subprocess
from pathlib import Path
from mpx_genai_sdk import Masterpiecex  # Import the SDK

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MasterpieceXDirect")

def parse_arguments():
    parser = argparse.ArgumentParser(description="MasterpieceX Direct Model Downloader")
    parser.add_argument("--url", type=str, required=True,
                      help="MasterpieceX URL (like https://app.masterpiecex.com/generate/history/[ID])")
    parser.add_argument("--name", type=str, default=None,
                      help="Custom name for the downloaded model (default: extracted from URL)")
    parser.add_argument("--output_folder", type=str, default="output",
                      help="Folder to save outputs")
    parser.add_argument("--format", type=str, default="obj", choices=["obj", "glb", "all"],
                      help="Format to download (obj, glb, or all)")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    parser.add_argument("--api_key", type=str, default=None, 
                      help="MasterpieceX API key (defaults to MPX_API_KEY environment variable)")
    parser.add_argument("--force", action="store_true",
                      help="Force redownload even if files already exist")
    parser.add_argument("--blender_executable", type=str, default=None,
                      help="Path to Blender executable (for format conversion)")
    return parser.parse_args()

def extract_id_from_url(url):
    """Extract the unique ID from a MasterpieceX URL"""
    # Extract the ID from the URL path
    parts = url.strip('/').split('/')
    return parts[-1]

def get_model_name_from_id(model_id):
    """Generate a model name from the ID"""
    return f"mpx_model_{model_id}"

def ensure_output_folder(folder_path):
    """Create output folder if it doesn't exist"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.info(f"Created output folder: {folder_path}")
    return folder_path

def download_file(url, output_path):
    """Download a file from a URL to the specified path"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded file to: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        if logger.level == logging.DEBUG:
            import traceback
            traceback.print_exc()
        return None

def find_blender_executable():
    """Attempt to find the Blender executable on the system"""
    # Common locations for Blender
    if sys.platform == "darwin":  # macOS
        common_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender")
        ]
    elif sys.platform == "win32":  # Windows
        common_paths = [
            "C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 3.5\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 3.4\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 3.3\\blender.exe",
        ]
    else:  # Linux and others
        common_paths = [
            "/usr/bin/blender",
            "/usr/local/bin/blender",
        ]
    
    # Try to find blender in the common paths
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # If not found in common paths, try using 'which' on Unix-like systems
    if sys.platform != "win32":
        try:
            result = subprocess.run(["which", "blender"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
    
    return None

def convert_fbx_to_glb(fbx_path, blender_executable=None):
    """Convert FBX to GLB using Blender"""
    if not blender_executable:
        blender_executable = find_blender_executable()
        if not blender_executable:
            logger.error("Could not find Blender executable for conversion. Please specify with --blender_executable")
            return None
    
    # Create a temporary Python script for Blender to execute
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as script_file:
        script_path = script_file.name
        script_file.write('''
import bpy
import os
import sys

# Get command line arguments after the script name
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # Get all arguments after "--"

if len(argv) < 2:
    print("Error: Need input FBX and output GLB paths")
    sys.exit(1)

fbx_path = argv[0]
glb_path = argv[1]

# Clear the scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import FBX
bpy.ops.import_scene.fbx(filepath=fbx_path)

# Export as GLB
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    export_materials='EXPORT',
    export_colors=True,
    export_cameras=True,
    export_lights=True,
    export_extras=True
)

print(f"Successfully converted {fbx_path} to {glb_path}")
''')
    
    # Get output path for GLB based on the FBX path
    glb_path = os.path.splitext(fbx_path)[0] + ".glb"
    
    try:
        # Call Blender with the script
        logger.info(f"Converting {fbx_path} to GLB using Blender...")
        result = subprocess.run([
            blender_executable,
            "--background",
            "--python", script_path,
            "--",  # Signal the end of Blender args and the beginning of script args
            fbx_path,
            glb_path
        ], capture_output=True, text=True)
        
        # Clean up the script
        os.unlink(script_path)
        
        # Check if the conversion was successful
        if result.returncode != 0:
            logger.error(f"Blender conversion failed: {result.stderr}")
            return None
        
        if not os.path.exists(glb_path):
            logger.error(f"GLB file was not created at expected path: {glb_path}")
            return None
        
        logger.info(f"Successfully converted FBX to GLB: {glb_path}")
        return glb_path
        
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        if logger.level == logging.DEBUG:
            import traceback
            traceback.print_exc()
        return None
    finally:
        # Make sure the script is deleted
        if os.path.exists(script_path):
            os.unlink(script_path)

def get_model_info_using_sdk(model_id, api_key):
    """Get model information using the MPX SDK"""
    try:
        # Initialize the SDK client
        client = Masterpiecex(bearer_token=api_key)
        
        # Use the SDK to retrieve the status of the generation
        logger.info(f"Fetching model information for ID: {model_id}")
        status_response = client.status.retrieve(model_id)
        
        # Check if the status is completed
        if status_response.status != "complete":
            logger.error(f"Model generation not complete. Current status: {status_response.status}")
            return None
        
        # Return the outputs object that contains all download URLs
        return status_response.outputs
    
    except Exception as e:
        logger.error(f"Error getting model information: {str(e)}")
        if logger.level == logging.DEBUG:
            import traceback
            traceback.print_exc()
        return None

def main():
    args = parse_arguments()
    
    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Parse the URL to get the ID
    model_id = extract_id_from_url(args.url)
    if not model_id:
        logger.error(f"Could not extract model ID from URL: {args.url}")
        sys.exit(1)
    
    logger.info(f"Extracted model ID: {model_id}")
    
    # Set model name
    model_name = args.name if args.name else get_model_name_from_id(model_id)
    logger.info(f"Using model name: {model_name}")
    
    # Create specific output folder for this model
    output_folder = os.path.join(args.output_folder, model_name)
    ensure_output_folder(output_folder)
    
    # Check if files already exist
    if not args.force:
        existing_files = []
        if args.format == "obj" or args.format == "all":
            existing_files.extend(list(Path(output_folder).glob("**/*.obj")))
            existing_files.extend(list(Path(output_folder).glob("**/*.fbx")))  # Also check for FBX
        if args.format == "glb" or args.format == "all":
            existing_files.extend(list(Path(output_folder).glob("**/*.glb")))
        
        if existing_files:
            logger.info(f"Found {len(existing_files)} existing model files in {output_folder}:")
            for file in existing_files:
                logger.info(f"  - {file}")
            logger.info("Use --force to redownload")
            
            logger.info(f"\n🎉 Model '{model_name}' is already available")
            logger.info(f"📂 Located at: {os.path.abspath(output_folder)}")
            
            # Suggest next steps
            logger.info("\nNext steps:")
            logger.info("1. Import into Blender manually, or")
            logger.info("2. Create a Three.js animation:")
            logger.info(f"   python threejs_animation.py --obj_path \"{os.path.abspath(existing_files[0])}\" --animation_type bounce")
            
            sys.exit(0)
    
    # Get API key
    api_key = args.api_key or os.environ.get("MPX_API_KEY")
    if not api_key:
        logger.error("No API key provided. Please set MPX_API_KEY environment variable or use --api_key")
        sys.exit(1)
    
    # Make sure the SDK can find the bearer token
    os.environ["MPX_SDK_BEARER_TOKEN"] = api_key
    
    # Get model information using the SDK
    model_outputs = get_model_info_using_sdk(model_id, api_key)
    if not model_outputs:
        logger.error("Failed to get model information")
        sys.exit(1)
    
    # Download the requested file formats
    downloaded_files = []
    fbx_path = None
    
    # Process available formats
    if args.format == "obj" or args.format == "all" or (args.format == "glb" and not model_outputs.glb):
        if model_outputs.fbx:
            fbx_path = os.path.join(output_folder, f"{model_name}.fbx")
            if download_file(model_outputs.fbx, fbx_path):
                downloaded_files.append(fbx_path)
                logger.info(f"Downloaded FBX file: {fbx_path}")
    
    if args.format == "glb" or args.format == "all":
        glb_downloaded = False
        
        # First try to download GLB directly if available
        if model_outputs.glb:
            glb_path = os.path.join(output_folder, f"{model_name}.glb")
            if download_file(model_outputs.glb, glb_path):
                downloaded_files.append(glb_path)
                logger.info(f"Downloaded GLB file: {glb_path}")
                glb_downloaded = True
        
        # If GLB not available but FBX is, try to convert
        elif fbx_path and os.path.exists(fbx_path):
            logger.info("GLB format not available directly. Attempting to convert from FBX...")
            glb_path = convert_fbx_to_glb(fbx_path, args.blender_executable)
            
            if glb_path and os.path.exists(glb_path):
                downloaded_files.append(glb_path)
                logger.info(f"Created GLB file via conversion: {glb_path}")
                glb_downloaded = True
        
        if not glb_downloaded and args.format == "glb":
            logger.warning("Unable to get or create GLB format. No GLB file available or conversion failed.")
    
    # Also download the thumbnail if available
    if model_outputs.thumbnail:
        thumb_path = os.path.join(output_folder, f"{model_name}_thumbnail.png")
        if download_file(model_outputs.thumbnail, thumb_path):
            logger.info(f"Downloaded thumbnail: {thumb_path}")
    
    # Check if we downloaded any files
    if downloaded_files:
        logger.info(f"\n🎉 Process completed for model '{model_name}'")
        logger.info(f"📂 Check the output at: {os.path.abspath(output_folder)}")
        
        # Suggest next steps
        logger.info("\nNext steps:")
        logger.info("1. Import into Blender manually, or")
        logger.info("2. Create a Three.js animation:")
        logger.info(f"   python threejs_animation.py --obj_path \"{os.path.abspath(downloaded_files[0])}\" --animation_type bounce")
    else:
        logger.error("Failed to download any model files")
        sys.exit(1)

if __name__ == "__main__":
    main() 