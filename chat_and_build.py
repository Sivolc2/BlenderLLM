#!/usr/bin/env python3
"""
Interactive Chat and Build for BlenderLLM
-----------------------------------------
An interactive CLI that allows users to have a conversation about 3D models
and seamlessly build them when ready.
"""

import os
import sys
import argparse
import platform
import readline  # For better CLI input experience
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
    
    parser = argparse.ArgumentParser(description="Interactive Chat and Build with BlenderLLM")
    parser.add_argument("--model_name", type=str, default="openai:gpt-4",
                      help="Model to use (default: openai:gpt-4)")
    parser.add_argument("--output_folder", type=str, default="output",
                      help="Folder to save outputs")
    parser.add_argument("--blender_executable", type=str, default=default_blender,
                      help=f"Path to Blender executable (default: {default_blender})")
    parser.add_argument("--brightness", type=str, default="Medium Bright", 
                      choices=BRIGHTNESS.keys(), 
                      help="Brightness level for rendering")
    return parser.parse_args()

def generate_obj_name_from_prompt(prompt):
    """Generate a filename-safe object name from the prompt"""
    words = prompt.split()[:3]  # Take first 3 words
    name = "_".join(words).lower()
    
    # Remove non-alphanumeric characters except underscores
    safe_name = "".join(c for c in name if c.isalnum() or c == "_")
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = "blender_model"
        
    return safe_name

def ensure_output_folder_exists(folder_path):
    """Create output folder if it doesn't exist"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def clear_screen():
    """Clear the terminal screen based on OS"""
    os.system('cls' if os.name == 'nt' else 'clear')

def build_model(prompt, model_name, obj_name, output_folder, blender_executable, brightness):
    """Build a 3D model from the prompt"""
    # Create specific output folder for this object
    object_output_folder = os.path.join(output_folder, obj_name)
    ensure_output_folder_exists(object_output_folder)
    
    # Generate script
    print(f"\nGenerating script for: '{prompt}'")
    script = generate_response(model_name, prompt)
    
    # Execute script to create .obj file
    print(f"Creating 3D model...")
    run_blender_script(
        script, 
        obj_name, 
        object_output_folder, 
        [], 
        [], 
        (), 
        blender_executable, 
        save_obj=True
    )
    obj_path = os.path.join(object_output_folder, f"{obj_name}.obj")
    print(f"✅ Object created and saved to {obj_path}")
    
    # Render images
    print("Rendering images from multiple angles...")
    try:
        bounding_coords = calculate_bounding_box(obj_path)
        brightness_value = BRIGHTNESS.get(brightness, BRIGHTNESS["Medium Bright"])
        run_blender_script(
            script,
            obj_name,
            object_output_folder,
            bounding_coords,
            CAMERA_ANGLES,
            brightness_value,
            blender_executable,
            save_image=True,
        )
        print(f"✅ Images rendered and saved to {object_output_folder}")
    except Exception as e:
        print(f"⚠️ Warning: Error rendering images: {str(e)}")
    
    print(f"\n🎉 All done! Your model '{obj_name}' is ready.")
    print(f"📂 Check the output at: {os.path.abspath(object_output_folder)}")
    
    return object_output_folder

def display_welcome():
    """Display welcome message and instructions"""
    clear_screen()
    print("=" * 60)
    print("🔨 BlenderLLM Interactive Chat and Build 🔨".center(60))
    print("=" * 60)
    print("\nDescribe the 3D model you want to create, then use commands to build it.")
    print("\nCommands:")
    print("  /build [name]  - Build the model (optional: specify object name)")
    print("  /clear         - Clear the screen")
    print("  /exit or /quit - Exit the program")
    print("  /help          - Show this help message")
    print("\nStart by describing what 3D model you want to create...\n")

def main():
    args = parse_arguments()
    
    # Ensure Blender executable exists
    if not os.path.exists(args.blender_executable) and '/' in args.blender_executable:
        print(f"⚠️ Warning: Blender executable not found at {args.blender_executable}")
        print("Trying system path 'blender' command instead...")
        args.blender_executable = "blender"
    
    display_welcome()
    
    current_prompt = ""
    while True:
        try:
            user_input = input("\n> ").strip()
            
            # Handle commands
            if user_input.startswith("/"):
                command = user_input.split()[0].lower()
                
                if command in ["/exit", "/quit"]:
                    print("Goodbye!")
                    sys.exit(0)
                
                elif command == "/clear":
                    clear_screen()
                
                elif command == "/help":
                    print("\nCommands:")
                    print("  /build [name]  - Build the model (optional: specify object name)")
                    print("  /clear         - Clear the screen")
                    print("  /exit or /quit - Exit the program")
                    print("  /help          - Show this help message")
                
                elif command == "/build":
                    if not current_prompt:
                        print("⚠️ Please describe a model first before building.")
                        continue
                    
                    # Get object name from command or generate from prompt
                    parts = user_input.split(maxsplit=1)
                    if len(parts) > 1 and parts[1].strip():
                        obj_name = parts[1].strip()
                    else:
                        obj_name = generate_obj_name_from_prompt(current_prompt)
                        print(f"Auto-generated object name: {obj_name}")
                    
                    # Build the model
                    output_path = build_model(
                        current_prompt, 
                        args.model_name, 
                        obj_name, 
                        args.output_folder, 
                        args.blender_executable, 
                        args.brightness
                    )
                    
                    # Reset for next model
                    current_prompt = ""
                    print("\nReady for your next model description!")
                
                else:
                    print(f"Unknown command: {command}")
                    print("Type /help for available commands")
            
            # Regular input - add to current prompt
            else:
                if not user_input:
                    continue
                    
                if current_prompt:
                    # Append to existing prompt
                    current_prompt += " " + user_input
                    print("Description updated. Type /build when ready to create your model.")
                else:
                    # New prompt
                    current_prompt = user_input
                    print("Description captured. Type /build when ready to create your model.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 