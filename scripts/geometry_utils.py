import math
import itertools
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlenderLLM.geometry")

def parse_obj_file(file_path):
    """Parse a Wavefront OBJ file to extract vertex coordinates."""
    vertices = []
    
    if not os.path.exists(file_path):
        logger.error(f"OBJ file not found: {file_path}")
        return vertices
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        logger.error(f"OBJ file is empty: {file_path}")
        return vertices
    
    logger.info(f"Parsing OBJ file: {file_path} (size: {file_size} bytes)")
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('v '):  # Vertex line
                    parts = line.split()
                    if len(parts) >= 4:  # v x y z
                        try:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            vertices.append((x, y, z))
                        except ValueError as e:
                            logger.warning(f"Could not parse vertex coordinates: {line.strip()}, error: {str(e)}")
        
        logger.info(f"Extracted {len(vertices)} vertices from OBJ file")
        return vertices
    except Exception as e:
        logger.error(f"Error parsing OBJ file: {str(e)}")
        return []

def calculate_bounding_box(file_path):
    """Calculate the bounding box coordinates from vertices in an OBJ file."""
    vertices = parse_obj_file(file_path)
    
    if not vertices:
        logger.warning(f"No vertices found in file: {file_path}, using default bounding box")
        # Return default coordinates for camera placement
        return default_camera_coordinates()
    
    # Calculate min and max coordinates
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    
    for x, y, z in vertices:
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
        min_z, max_z = min(min_z, z), max(max_z, z)
    
    # Log bounding box dimensions
    width = max_x - min_x
    height = max_y - min_y
    depth = max_z - min_z
    logger.info(f"Calculated bounding box: [{min_x:.2f}, {min_y:.2f}, {min_z:.2f}] to [{max_x:.2f}, {max_y:.2f}, {max_z:.2f}]")
    logger.info(f"Dimensions: width={width:.2f}, height={height:.2f}, depth={depth:.2f}")
    
    # Calculate center and maximum size
    delta_max = max(max_x - min_x, max_y - min_y, max_z - min_z)
    center = [(max_x + min_x) / 2, (max_y + min_y) / 2, (max_z + min_z) / 2]
    
    # Generate camera coordinates with proper scale factor
    factor = 2.5 / math.sqrt(2)
    coords = []
    
    # Generate 8 camera positions around the model (for backward compatibility)
    for i, j, k in itertools.product([-1, 1], repeat=3):
        x = center[0] + i * delta_max * factor
        y = center[2] + j * delta_max * factor  # Note: z and y are swapped in Blender
        z = center[1] + k * delta_max * 2.5
        coords.append((x, y, z))
    
    # For debugging info, also provide raw bounding box data
    # Store as attribute that can be accessed if needed
    calculate_bounding_box.raw_bounds = (min_x, min_y, min_z, max_x, max_y, max_z)
    calculate_bounding_box.center = center
    calculate_bounding_box.size = delta_max
    
    return coords

def default_camera_coordinates():
    """Return default camera coordinates when bounding box can't be calculated."""
    logger.info("Using default camera coordinates")
    
    # Default coordinates for 8 camera positions
    coords = []
    factor = 2.5 / math.sqrt(2)
    for i, j, k in itertools.product([-1, 1], repeat=3):
        x = i * factor
        y = j * factor
        z = k * 2.5
        coords.append((x, y, z))
    
    return coords
