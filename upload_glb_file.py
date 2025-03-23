#!/usr/bin/env python3
"""
GLB File Uploader for Redpanda
------------------------------
A script that uploads GLB 3D model files to Redpanda.
"""

import os
import sys
import json
import time
import base64
import logging
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GLBUploader")

# Redpanda connection settings
BOOTSTRAP_SERVERS = os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", 
                                 "cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092")
USERNAME = os.environ.get("REDPANDA_CLOUD_USERNAME", "backend")
PASSWORD = os.environ.get("REDPANDA_CLOUD_PASSWORD", "jQZzu9x3z0WKsjWLmE9ZLf44fKoXag")
TOPIC = os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "geojson-data")

# The default GLB file to upload (from output folder)
DEFAULT_GLB_FILE = "output/mpx_model_QpozDiykmQpVEsH8iZ2Y/mpx_model_QpozDiykmQpVEsH8iZ2Y.glb"

def get_kafka_config():
    """Create Kafka configuration"""
    config = {
        "bootstrap_servers": BOOTSTRAP_SERVERS,
        "security_protocol": "SASL_SSL",
        "sasl_mechanism": "SCRAM-SHA-256",
        "sasl_plain_username": USERNAME,
        "sasl_plain_password": PASSWORD,
    }
    return config

def upload_glb_file(glb_file_path=None):
    """Upload a GLB file to Redpanda"""
    file_path = Path(glb_file_path or DEFAULT_GLB_FILE)
    
    if not file_path.exists():
        logger.error(f"GLB file not found: {file_path}")
        sys.exit(1)
    
    try:
        # Create producer
        logger.info(f"Connecting to Redpanda at {BOOTSTRAP_SERVERS}")
        producer_config = get_kafka_config()
        producer = KafkaProducer(
            **producer_config,
            value_serializer=lambda m: json.dumps(m).encode('utf-8'),
            max_request_size=20971520,  # 20MB max message size (increased from 10MB)
            buffer_memory=33554432,     # 32MB buffer memory
            compression_type="gzip"     # Use compression to reduce message size
        )
        logger.info("✅ Connected successfully!")
        
        # Read binary GLB file
        logger.info(f"Reading GLB file: {file_path}")
        with open(file_path, 'rb') as f:
            binary_content = f.read()
        
        # Get file size
        file_size = len(binary_content)
        logger.info(f"GLB file size: {file_size} bytes")
        
        # Encode binary content as base64
        b64_content = base64.b64encode(binary_content).decode('utf-8')
        
        # Create message with file metadata
        model_id = file_path.stem
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        message = {
            "model_id": model_id,
            "timestamp": timestamp,
            "filename": file_path.name,
            "file_size": file_size,
            "content_type": "model/gltf-binary",
            "encoding": "base64",
            "data": b64_content
        }
        
        # Create unique message key
        message_key = f"{model_id}-{timestamp}".encode('utf-8')
        logger.info(f"Sending GLB file to topic: {TOPIC}")
        
        # Send message
        future = producer.send(
            TOPIC,
            key=message_key,
            value=message,
            headers=[
                ('content-type', b'application/json'),
                ('model-id', model_id.encode('utf-8')),
                ('file-type', b'glb')
            ]
        )
        
        # Wait for the send operation to complete
        metadata = future.get(timeout=60)  # Longer timeout for large files
        logger.info(f"✅ GLB file sent to partition {metadata.partition} at offset {metadata.offset}")
        
        # Flush and close producer
        producer.flush()
        producer.close()
        
        logger.info("✅ Successfully uploaded GLB file to Redpanda")
        
    except Exception as e:
        logger.error(f"Error uploading GLB file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Check if a file path is provided as argument
    if len(sys.argv) > 1:
        upload_glb_file(sys.argv[1])
    else:
        # Use default GLB file
        upload_glb_file() 