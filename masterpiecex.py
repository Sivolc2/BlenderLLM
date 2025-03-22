#!/usr/bin/env python3
"""
MasterpieceX 3D Generator
-------------------------
Generate 3D models using the MasterpieceX API and download them for use in Blender.
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
from pathlib import Path
from mpx_genai_sdk import Masterpiecex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MasterpieceX")

def parse_arguments():
    parser = argparse.ArgumentParser(description="MasterpieceX 3D Model Generator")
    parser.add_argument("--prompt", type=str, required=True,
                      help="Text prompt describing what to create")
    parser.add_argument("--output_folder", type=str, default="output",
                      help="Folder to save outputs")
    parser.add_argument("--poll_interval", type=int, default=10,
                      help="Time in seconds between status checks")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    parser.add_argument("--max_wait", type=int, default=600,
                      help="Maximum time to wait for generation in seconds (default: 10 minutes)")
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
            return obj_files[0]  # Return the first OBJ file
        else:
            logger.warning("No OBJ files found in the extracted content.")
            return None
    
    except Exception as e:
        logger.error(f"Error downloading or extracting model: {str(e)}")
        return None

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
    return Path(output_path)

def main():
    args = parse_arguments()
    
    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Check if in simulation mode
    if args.simulate:
        logger.info("Running in simulation mode - no API calls will be made")
    else:
        # Check if API key is set
        api_key = os.environ.get("MPX_API_KEY")
        
        if args.debug:
            # Print environment variable info for debugging
            logger.debug(f"MPX_API_KEY environment variable: {'SET' if api_key else 'NOT SET'}")
            if api_key:
                logger.debug(f"MPX_API_KEY length: {len(api_key)} characters")
                logger.debug(f"MPX_API_KEY first/last chars: {api_key[:5]}...{api_key[-5:]}")
            
            # Check for SDK bearer token variable
            sdk_token = os.environ.get("MPX_SDK_BEARER_TOKEN")
            logger.debug(f"MPX_SDK_BEARER_TOKEN environment variable: {'SET' if sdk_token else 'NOT SET'}")
        
        if not api_key:
            logger.error("MPX_API_KEY environment variable is not set. Please set it with your MasterpieceX API key.")
            logger.error("Run: export MPX_API_KEY='your_api_key_here'")
            sys.exit(1)
        
        # Set bearer token environment variable expected by the SDK (force-set it even if already set)
        os.environ["MPX_SDK_BEARER_TOKEN"] = api_key
        logger.debug("Set MPX_SDK_BEARER_TOKEN from MPX_API_KEY")
    
    # Generate model name from prompt
    model_name = get_obj_name_from_prompt(args.prompt)
    
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
            logger.info(f"\n🎉 Simulation completed for model '{model_name}'")
            logger.info(f"📂 Check the output at: {os.path.abspath(output_folder)}")
            
            # Suggest next steps
            logger.info("\nNext steps:")
            logger.info("1. Import the OBJ file into Blender manually, or")
            logger.info("2. Use seamless_builder.py to render images of the model:")
            logger.info(f"   python seamless_builder.py --prompt \"{args.prompt}\" --obj_name \"{model_name}\" --skip_render=False")
        else:
            logger.error("Simulation failed to create an OBJ file")
            sys.exit(1)
        
        return  # End simulation early
    
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
        
        # Find the GLB file
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
            logger.info(f"\n🎉 Process completed for model '{model_name}'")
            logger.info(f"📂 Check the output at: {os.path.abspath(output_folder)}")
            
            # Suggest next steps
            logger.info("\nNext steps:")
            logger.info("1. Import the OBJ file into Blender manually, or")
            logger.info("2. Use seamless_builder.py to render images of the model:")
            logger.info(f"   python seamless_builder.py --prompt \"{args.prompt}\" --obj_name \"{model_name}\" --skip_render=False")
        else:
            logger.error("Failed to download or extract the model")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
