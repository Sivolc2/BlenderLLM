#!/usr/bin/env python3
"""
Simple Text File Writer
----------------------
Writes a simple text message to a file to verify basic functionality.
"""

import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SimpleText")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Write a simple text message to a file")
    parser.add_argument("--output_file", type=str, default="simple_message.json",
                      help="Output file path")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Create a simple message
    message = {
        "test": "Simple text test",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "This is a test message without any Kafka integration"
    }
    
    # Write to file
    output_path = Path(args.output_file)
    logger.info(f"Writing message to {output_path}")
    
    try:
        with open(output_path, 'w') as f:
            json.dump(message, f, indent=2)
        
        logger.info(f"✅ Message successfully written to {output_path}")
        logger.info(f"File size: {output_path.stat().st_size} bytes")
        
    except Exception as e:
        logger.error(f"Error writing to file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 