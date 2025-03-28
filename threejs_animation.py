#!/usr/bin/env python3
"""
Three.js Animation Exporter
--------------------------
This script takes a 3D model generated by MasterpieceX or BlenderLLM and creates 
a Three.js web page with animation.
"""

import os
import sys
import argparse
import logging
import json
import shutil
import base64
import webbrowser
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ThreeJS-Animator")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Three.js Animation</title>
    <style>
        body {{ margin: 0; overflow: hidden; }}
        canvas {{ display: block; }}
        #info {{
            position: absolute;
            top: 10px;
            width: 100%;
            text-align: center;
            color: white;
            font-family: Arial, sans-serif;
            pointer-events: none;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            width: 100%;
            text-align: center;
            color: white;
            font-family: Arial, sans-serif;
            font-size: 18px;
        }}
        #error {{
            position: absolute;
            top: 50%;
            width: 100%;
            padding: 20px;
            text-align: center;
            color: #ff5555;
            background-color: rgba(0,0,0,0.7);
            font-family: Arial, sans-serif;
            font-size: 16px;
            display: none;
        }}
    </style>
</head>
<body>
    <div id="info">{title} - Press A to toggle animation, Space to reset view</div>
    <div id="loading">Loading model...</div>
    <div id="error"></div>
    <script type="importmap">
        {{
            "imports": {{
                "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
                "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
            }}
        }}
    </script>
    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ OBJLoader }} from 'three/addons/loaders/OBJLoader.js';
        
        // Error handler
        function showError(message) {{
            const errorEl = document.getElementById('error');
            errorEl.textContent = 'Error: ' + message;
            errorEl.style.display = 'block';
            document.getElementById('loading').style.display = 'none';
        }}
        
        try {{
            // Scene setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color({scene_color});
            
            // Camera setup
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set({camera_x}, {camera_y}, {camera_z});
            
            // Renderer setup
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.body.appendChild(renderer.domElement);
            
            // Controls
            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Reset view handler
            window.addEventListener('keydown', (event) => {{
                if (event.code === 'Space') {{
                    camera.position.set({camera_x}, {camera_y}, {camera_z});
                    controls.target.set(0, 0, 0);
                    controls.update();
                }}
            }});
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, {ambient_intensity});
            scene.add(ambientLight);
            
            const dirLight = new THREE.DirectionalLight(0xffffff, {directional_intensity});
            dirLight.position.set(5, 10, 5);
            dirLight.castShadow = true;
            dirLight.shadow.mapSize.width = 1024;
            dirLight.shadow.mapSize.height = 1024;
            scene.add(dirLight);
            
            // Animation system
            const clock = new THREE.Clock();
            let mixer;
            let model;
            let animationPlaying = true; // Start with animation on
            
            // Load 3D model (embedded to avoid CORS issues)
            function loadModel() {{
                try {{
                    const objLoader = new OBJLoader();
                    
                    // Load the model directly from the embedded OBJ data
                    const objData = `{obj_data}`;
                    
                    if (!objData || objData.trim() === '') {{
                        throw new Error('Model data is empty');
                    }}
                    
                    model = objLoader.parse(objData);
                    
                    // Scale and position the model
                    const box = new THREE.Box3().setFromObject(model);
                    if (box.isEmpty()) {{
                        throw new Error('Model has no geometry or is empty');
                    }}
                    
                    const size = box.getSize(new THREE.Vector3()).length();
                    const center = box.getCenter(new THREE.Vector3());
                    
                    model.position.x = -center.x;
                    model.position.y = -center.y;
                    model.position.z = -center.z;
                    
                    // Apply scale to fit the model
                    const scale = {model_scale} / size;
                    model.scale.set(scale, scale, scale);
                    
                    // Add default material if model has none
                    model.traverse((child) => {{
                        if (child.isMesh) {{
                            if (!child.material || child.material.type === 'MeshBasicMaterial') {{
                                child.material = new THREE.MeshPhongMaterial({{ 
                                    color: 0xcccccc, 
                                    shininess: 30,
                                    flatShading: false 
                                }});
                            }}
                            child.castShadow = true;
                            child.receiveShadow = true;
                        }}
                    }});
                    
                    // Setup animation
                    setupAnimation(model);
                    
                    scene.add(model);
                    console.log("Model loaded successfully");
                    
                    // Hide loading message
                    document.getElementById('loading').style.display = 'none';
                }} catch (error) {{
                    console.error('Error parsing model:', error);
                    showError(error.message || 'Failed to load model');
                }}
            }}
            
            // Setup animation
            function setupAnimation(model) {{
                // Define animations - here we'll use a simple rotation
                const animations = [];
                
                // Create a simple rotation animation
                const rotationKF = new THREE.AnimationClip('rotation', {animation_duration}, [
                    // Rotation on Y axis
                    new THREE.KeyframeTrack(
                        '.rotation[y]', 
                        [0, {animation_duration}],
                        [0, Math.PI * 2]
                    ),
                    // Optional: Add a bounce effect by moving up and down
                    new THREE.KeyframeTrack(
                        '.position[y]',
                        [0, {animation_duration} / 2, {animation_duration}],
                        [0, {bounce_height}, 0]
                    )
                ]);
                
                animations.push(rotationKF);
                
                // Create animation mixer
                mixer = new THREE.AnimationMixer(model);
                
                // Add all animations to the mixer
                animations.forEach((clip) => {{
                    const action = mixer.clipAction(clip);
                    action.setLoop(THREE.LoopRepeat);
                    action.clampWhenFinished = true;
                    action.enabled = true;
                    action.timeScale = 1;
                    action.play();
                    // Start with animation playing
                    action.paused = false;
                }});
            }}
            
            // Animation toggle
            window.addEventListener('keydown', (event) => {{
                if (event.key.toLowerCase() === 'a') {{
                    animationPlaying = !animationPlaying;
                    
                    if (mixer) {{
                        mixer._actions.forEach((action) => {{
                            action.paused = !animationPlaying;
                        }});
                    }}
                }}
            }});
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }});
            
            // Create a ground plane
            const groundGeometry = new THREE.PlaneGeometry(100, 100);
            const groundMaterial = new THREE.MeshPhongMaterial({{ 
                color: 0x999999, 
                shininess: 0,
                side: THREE.DoubleSide
            }});
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -2;
            ground.receiveShadow = true;
            scene.add(ground);
            
            // Add grid helper
            const gridHelper = new THREE.GridHelper(20, 20, 0x555555, 0x333333);
            gridHelper.position.y = -1.999;
            scene.add(gridHelper);
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                
                controls.update();
                
                if (mixer && animationPlaying) {{
                    mixer.update(clock.getDelta());
                }}
                
                renderer.render(scene, camera);
            }}
            
            // Start the process
            loadModel();
            animate();
            
        }} catch (e) {{
            console.error("Critical error:", e);
            showError(e.message || 'An unexpected error occurred');
        }}
    </script>
</body>
</html>
"""

def parse_arguments():
    parser = argparse.ArgumentParser(description="Three.js Animation Exporter")
    parser.add_argument("--obj_path", type=str, required=True,
                      help="Path to the OBJ file")
    parser.add_argument("--output_dir", type=str, default=None,
                      help="Output directory for the web page (defaults to same as OBJ)")
    parser.add_argument("--title", type=str, default=None,
                      help="Title for the web page (defaults to OBJ filename)")
    parser.add_argument("--animation_type", type=str, default="rotate",
                      choices=["rotate", "bounce", "spin"],
                      help="Type of animation to apply")
    parser.add_argument("--camera_distance", type=float, default=5.0,
                      help="Camera distance from the model")
    parser.add_argument("--scene_color", type=str, default="0x1a1a1a",
                      help="Background color of the scene (hex code)")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    parser.add_argument("--open_browser", action="store_true",
                      help="Automatically open the result in a web browser")
    parser.add_argument("--start_server", action="store_true",
                      help="Start a local web server to avoid CORS issues (port 8000)")
    return parser.parse_args()

def ensure_output_dir(output_dir):
    """Create output directory if it doesn't exist"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    return output_dir

def create_threejs_scene(obj_path, output_dir, title, animation_type, camera_distance, scene_color, debug=False):
    """Create a Three.js scene with the specified model and animation"""
    # Set logging level
    if debug:
        logger.setLevel(logging.DEBUG)
    
    # Validate OBJ file exists
    if not os.path.exists(obj_path):
        logger.error(f"OBJ file not found: {obj_path}")
        return False
    
    # Prepare output directory and file paths
    obj_filename = os.path.basename(obj_path)
    obj_name_base = os.path.splitext(obj_filename)[0]
    
    if not title:
        title = obj_name_base.replace("_", " ").title()
    
    if not output_dir:
        output_dir = os.path.dirname(os.path.abspath(obj_path))
    
    ensure_output_dir(output_dir)
    
    # Set animation parameters based on type
    animation_duration = 5.0  # seconds
    bounce_height = 0.5
    model_scale = 2.0
    
    if animation_type == "bounce":
        bounce_height = 1.0
        animation_duration = 2.0
    elif animation_type == "spin":
        model_scale = 1.5
        animation_duration = 3.0
    
    # Create the HTML file
    html_path = os.path.join(output_dir, f"{obj_name_base}_animated.html")
    
    # Read the OBJ file content for embedding
    try:
        with open(obj_path, 'r', encoding='utf-8', errors='replace') as f:
            obj_data = f.read().replace("\\", "\\\\").replace("`", "\\`")
        logger.debug(f"Read OBJ file: {len(obj_data)} bytes")
        
        # Check if file is empty or too small
        if len(obj_data) < 10:  # Arbitrary minimum size for a valid OBJ
            logger.warning(f"OBJ file appears to be too small or empty: {len(obj_data)} bytes")
    except Exception as e:
        logger.error(f"Failed to read OBJ file: {e}")
        return False
    
    # Calculate camera position based on distance
    camera_x = 0
    camera_y = camera_distance * 0.5
    camera_z = camera_distance
    
    # Set lighting parameters
    ambient_intensity = 0.5
    directional_intensity = 0.8
    
    # Fill in the HTML template
    html_content = HTML_TEMPLATE.format(
        title=title,
        obj_filename=obj_filename,
        obj_data=obj_data,
        scene_color=scene_color,
        camera_x=camera_x,
        camera_y=camera_y,
        camera_z=camera_z,
        model_scale=model_scale,
        animation_duration=animation_duration,
        bounce_height=bounce_height,
        ambient_intensity=ambient_intensity,
        directional_intensity=directional_intensity
    )
    
    # Write the HTML file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Created Three.js animation scene at: {html_path}")
    logger.info(f"Open this file in a web browser to view the animated model")
    logger.info(f"Press 'A' key to toggle animation (on by default)")
    logger.info(f"Press 'Space' key to reset the camera view")
    logger.info(f"Note: The OBJ data is embedded in the HTML file to avoid CORS issues")
    
    return html_path

def main():
    args = parse_arguments()
    
    # Create the Three.js scene
    html_path = create_threejs_scene(
        args.obj_path,
        args.output_dir,
        args.title,
        args.animation_type,
        args.camera_distance,
        args.scene_color,
        args.debug
    )
    
    if html_path:
        logger.info(f"\n🎉 Three.js animation created successfully!")
        file_path = os.path.abspath(html_path)
        logger.info(f"📂 HTML file saved to: {file_path}")
        
        if args.start_server:
            import http.server
            import socketserver
            import threading
            import socket
            
            # Get the directory containing the HTML file
            web_dir = os.path.dirname(file_path)
            os.chdir(web_dir)
            
            # Try different ports if the default is already in use
            ports = [8000, 8080, 8888, 9000, 9090]
            server_started = False
            
            for PORT in ports:
                try:
                    # Define the request handler
                    Handler = http.server.SimpleHTTPRequestHandler
                    
                    # Create the server
                    httpd = socketserver.TCPServer(("", PORT), Handler)
                    
                    # Start the server in a separate thread
                    server_thread = threading.Thread(target=httpd.serve_forever)
                    server_thread.daemon = True
                    server_thread.start()
                    
                    logger.info(f"🌐 Started local web server at http://localhost:{PORT}")
                    server_started = True
                    break
                except OSError as e:
                    if e.errno == 48:  # Address already in use
                        logger.warning(f"Port {PORT} is already in use, trying another port...")
                    else:
                        logger.error(f"Failed to start server on port {PORT}: {e}")
                        break
            
            if not server_started:
                logger.error("Could not start server on any available port. Please close some applications or manually serve the files.")
                logger.info("You can manually start a server with: python -m http.server")
                if args.open_browser:
                    logger.info(f"Opening file directly in browser (CORS issues may occur)...")
                    webbrowser.open(f"file://{file_path}")
                return
            
            # Open the browser to the file
            if args.open_browser:
                file_url = f"http://localhost:{PORT}/{os.path.basename(html_path)}"
                logger.info(f"🌐 Opening {file_url} in web browser...")
                webbrowser.open(file_url)
                
                # Keep the server running
                try:
                    logger.info("Server is running. Press Ctrl+C to stop.")
                    while True:
                        pass
                except KeyboardInterrupt:
                    logger.info("Server stopped.")
            else:
                logger.info(f"To view the model, open: http://localhost:{PORT}/{os.path.basename(html_path)}")
                logger.info("Server is running. Press Ctrl+C to stop.")
                try:
                    while True:
                        pass
                except KeyboardInterrupt:
                    logger.info("Server stopped.")
                
        elif args.open_browser:
            logger.info(f"🌐 Opening {file_path} in web browser...")
            webbrowser.open(f"file://{file_path}")
    else:
        logger.error("Failed to create Three.js animation")
        sys.exit(1)

if __name__ == "__main__":
    main() 