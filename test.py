#!/usr/bin/env python3
"""
Test script for BlenderLLM
-------------------------
This script demonstrates two ways to use BlenderLLM:
1. Chat-only mode: Generate Python script based on text prompt
2. Modeling mode: Generate and execute the script to create 3D models

Requirements:
- Blender installed and accessible in PATH
- BlenderLLM model downloaded
"""

import os
import argparse
import platform
from scripts.infer import generate_response
from scripts.blender_runner import run_blender_script
from scripts.geometry_utils import calculate_bounding_box
from scripts.config import CAMERA_ANGLES, BRIGHTNESS

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
                return path
    
    # Default to command name for Linux/Windows or if macOS paths not found
    return "blender"

def parse_arguments():
    default_blender = get_default_blender_path()
    
    parser = argparse.ArgumentParser(description="Test BlenderLLM functionality")
    parser.add_argument("--mode", type=str, choices=["chat", "render"], default="chat",
                      help="Mode to run: 'chat' for script generation only, 'render' to generate and execute")
    parser.add_argument("--model_name", type=str, default="FreedomIntelligence/BlenderLLM",
                      help="Model path or name (default: FreedomIntelligence/BlenderLLM)")
    parser.add_argument("--prompt", type=str, default="Create a simple house with a door and two windows.",
                      help="Text prompt describing what to create")
    parser.add_argument("--obj_name", type=str, default="test_object",
                      help="Name for the output object file (render mode only)")
    parser.add_argument("--output_folder", type=str, default="test_output",
                      help="Folder to save outputs (render mode only)")
    parser.add_argument("--blender_executable", type=str, default=default_blender,
                      help=f"Path to Blender executable (default: {default_blender})")
    parser.add_argument("--brightness", type=str, default="Medium Bright", 
                      choices=BRIGHTNESS.keys(), 
                      help="Brightness level for rendering")
    return parser.parse_args()

def ensure_output_folder_exists(folder_path):
    """Create output folder if it doesn't exist"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created output folder: {folder_path}")

def main():
    args = parse_arguments()
    
    # Ensure Blender executable exists
    if not os.path.exists(args.blender_executable) and '/' in args.blender_executable:
        print(f"⚠️ Warning: Blender executable not found at {args.blender_executable}")
        print("Trying system path 'blender' command instead...")
        args.blender_executable = "blender"
    
    # Generate the Blender Python script
    print(f"Generating script from prompt: '{args.prompt}'")
    script = generate_response(args.model_name, args.prompt)
    
    # Chat mode: just print the script
    if args.mode == "chat":
        print("\n==== Generated Blender Python Script ====\n")
        print(script)
        print("\n=========================================\n")
        return
    
    # Render mode: execute the script in Blender
    if args.mode == "render":
        # Ensure output folder exists
        ensure_output_folder_exists(args.output_folder)
        
        # Step 1: Save the object as .obj file
        print(f"Saving object as {args.obj_name}.obj...")
        run_blender_script(
            script, 
            args.obj_name, 
            args.output_folder, 
            [], 
            [], 
            (), 
            args.blender_executable, 
            save_obj=True
        )
        obj_path = os.path.join(args.output_folder, f"{args.obj_name}.obj")
        print(f"Object saved to {obj_path}")
        
        # Step 2: Calculate bounding box and render images
        print("Rendering images...")
        bounding_coords = calculate_bounding_box(obj_path)
        brightness_value = BRIGHTNESS.get(args.brightness, BRIGHTNESS["Medium Bright"])
        run_blender_script(
            script,
            args.obj_name,
            args.output_folder,
            bounding_coords,
            CAMERA_ANGLES,
            brightness_value,
            args.blender_executable,
            save_image=True,
        )
        print(f"Images saved to {args.output_folder}")
        print("Completed successfully!")

if __name__ == "__main__":
    main() 