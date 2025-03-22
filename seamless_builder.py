#!/usr/bin/env python3
"""
Seamless Builder for BlenderLLM
-------------------------------
This script integrates the chat model with execution in a single flow.
It generates a Blender script from a prompt and immediately renders it,
providing a seamless experience from text to 3D model.
"""

import os
import sys
import argparse
import platform
import logging
import traceback
from scripts.infer import generate_response
from scripts.blender_runner import run_blender_script
from scripts.geometry_utils import calculate_bounding_box
from scripts.config import CAMERA_ANGLES, BRIGHTNESS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlenderLLM.builder")

def get_default_blender_path():
    """Get the default Blender executable path based on the operating system"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        # Common macOS Blender installation paths
        mac_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender/Blender.app/Contents/MacOS/Blender",
            # Add more potential paths if needed
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
    
    parser = argparse.ArgumentParser(description="BlenderLLM Seamless Builder")
    parser.add_argument("--model_name", type=str, default="openai:gpt-4",
                      help="Model to use (local model path, 'openai:model-name', 'anthropic:claude-3-5-sonnet-20240620', or 'api:endpoint')")
    parser.add_argument("--prompt", type=str, required=True,
                      help="Text prompt describing what to create")
    parser.add_argument("--obj_name", type=str, default=None,
                      help="Name for the output object file (defaults to auto-generated from prompt)")
    parser.add_argument("--output_folder", type=str, default="output",
                      help="Folder to save outputs")
    parser.add_argument("--blender_executable", type=str, default=default_blender,
                      help=f"Path to Blender executable (default: {default_blender})")
    parser.add_argument("--brightness", type=str, default="Medium Bright", 
                      choices=BRIGHTNESS.keys(), 
                      help="Brightness level for rendering")
    parser.add_argument("--show_script", action="store_true",
                      help="Display the generated script before execution")
    parser.add_argument("--skip_render", action="store_true",
                      help="Skip rendering and only generate the .obj file")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging and save generated scripts to file")
    parser.add_argument("--log_level", type=str, default="INFO",
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Set the logging level")
    parser.add_argument("--keep_temp_scripts", action="store_true",
                      help="Keep temporary scripts for debugging purposes")
    return parser.parse_args()

def generate_obj_name_from_prompt(prompt):
    """Generate a filename-safe object name from the prompt"""
    # Take the first few words, replace spaces with underscores
    words = prompt.split()[:3]  # Take first 3 words
    name = "_".join(words).lower()
    
    # Remove any non-alphanumeric characters except underscores
    safe_name = "".join(c for c in name if c.isalnum() or c == "_")
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = "blender_model"
        
    return safe_name

def ensure_output_folder_exists(folder_path):
    """Create output folder if it doesn't exist"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.info(f"Created output folder: {folder_path}")
    return folder_path

def save_script_to_file(script, output_path):
    """Save the generated script to a file for debugging"""
    try:
        with open(output_path, 'w') as file:
            file.write(script)
        logger.info(f"Script saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save script: {str(e)}")

def main():
    args = parse_arguments()
    
    # Set logging level based on arguments
    log_level = logging.DEBUG if args.debug else getattr(logging, args.log_level)
    logging.getLogger("BlenderLLM").setLevel(log_level)
    
    # Ensure Blender executable exists
    if not os.path.exists(args.blender_executable) and '/' in args.blender_executable:
        logger.warning(f"Blender executable not found at {args.blender_executable}")
        logger.info("Trying system path 'blender' command instead...")
        args.blender_executable = "blender"
    
    # Generate object name if not provided
    if not args.obj_name:
        args.obj_name = generate_obj_name_from_prompt(args.prompt)
        logger.info(f"Auto-generated object name: {args.obj_name}")
    
    # Create specific output folder for this object
    object_output_folder = os.path.join(args.output_folder, args.obj_name)
    ensure_output_folder_exists(object_output_folder)
    
    # Generate script
    logger.info(f"Generating script from prompt: '{args.prompt}'")
    try:
        script = generate_response(args.model_name, args.prompt)
        
        # Save script for debugging if requested
        script_path = os.path.join(object_output_folder, f"{args.obj_name}_script.py")
        if args.debug or args.keep_temp_scripts:
            save_script_to_file(script, script_path)
        
        # Show script if requested
        if args.show_script or args.debug:
            print("\n==== Generated Blender Python Script ====\n")
            print(script)
            print("\n=========================================\n")
        
        # Execute script to create .obj file
        logger.info(f"Creating 3D model...")
        try:
            # Set environment variable to instruct blender_runner to keep scripts if requested
            if args.keep_temp_scripts:
                os.environ["BLENDER_KEEP_TEMP_SCRIPTS"] = "1"
                logger.info("Temporary scripts will be preserved")
            
            obj_path = run_blender_script(
                script, 
                args.obj_name, 
                object_output_folder, 
                [], 
                CAMERA_ANGLES, 
                BRIGHTNESS.get(args.brightness, BRIGHTNESS["Medium Bright"]), 
                args.blender_executable, 
                save_obj=True
            )
            
            # Verify the object file was created
            if os.path.exists(obj_path):
                logger.info(f"✅ Object created and saved to {obj_path}")
                
                # Render if not skipped
                if not args.skip_render:
                    logger.info("Calculating bounding box...")
                    try:
                        # Calculate bounding box
                        bounding_coords = calculate_bounding_box(obj_path)
                        
                        logger.info("Rendering images from multiple angles...")
                        brightness_value = BRIGHTNESS.get(args.brightness, BRIGHTNESS["Medium Bright"])
                        run_blender_script(
                            script,
                            args.obj_name,
                            object_output_folder,
                            bounding_coords,
                            CAMERA_ANGLES,
                            brightness_value,
                            args.blender_executable,
                            save_image=True,
                        )
                        logger.info(f"✅ Images rendered and saved to {object_output_folder}")
                    except Exception as e:
                        logger.error(f"Error during rendering: {str(e)}")
                        if args.debug:
                            traceback.print_exc()
            else:
                logger.error(f"❌ Failed to create object at {obj_path}")
                
            logger.info(f"\n🎉 Process completed for model '{args.obj_name}'")
            logger.info(f"📂 Check the output at: {os.path.abspath(object_output_folder)}")
                
        except Exception as e:
            logger.error(f"Error during Blender execution: {str(e)}")
            if args.debug:
                traceback.print_exc()
            else:
                logger.info("Run with --debug flag for more detailed error information")
                
            # Save script even if not in debug mode, to help with troubleshooting
            if not args.debug and not args.keep_temp_scripts:
                save_script_to_file(script, script_path)
                logger.info(f"Script saved to {script_path} for troubleshooting")
            
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during script generation: {str(e)}")
        if args.debug:
            traceback.print_exc()
        else:
            logger.info("Run with --debug flag for more detailed error information")
        sys.exit(1)

if __name__ == "__main__":
    main() 