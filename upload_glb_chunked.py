#!/usr/bin/env python3
"""
Chunked GLB File Uploader for Redpanda
--------------------------------------
A script that uploads large GLB 3D model files to Redpanda in chunks.
"""

import os
import sys
import json
import time
import math
import base64
import hashlib
import logging
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ChunkedGLBUploader")

# Redpanda connection settings
BOOTSTRAP_SERVERS = os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", 
                                 "cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092")
USERNAME = os.environ.get("REDPANDA_CLOUD_USERNAME", "backend")
PASSWORD = os.environ.get("REDPANDA_CLOUD_PASSWORD", "jQZzu9x3z0WKsjWLmE9ZLf44fKoXag")
TOPIC = os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "geojson-data")

# The default GLB file to upload (from output folder)
DEFAULT_GLB_FILE = "output/mpx_model_QpozDiykmQpVEsH8iZ2Y/mpx_model_QpozDiykmQpVEsH8iZ2Y.glb"

# Chunk size in bytes (100KB - smaller to prevent timeouts)
CHUNK_SIZE = 100 * 1024

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

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read the file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def upload_glb_file_chunked(glb_file_path=None, chunk_size=CHUNK_SIZE):
    """Upload a GLB file to Redpanda in chunks"""
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
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        logger.info("✅ Connected successfully!")
        
        # Get file size and calculate number of chunks
        file_size = file_path.stat().st_size
        num_chunks = math.ceil(file_size / chunk_size)
        logger.info(f"File size: {file_size} bytes")
        logger.info(f"Chunk size: {chunk_size} bytes")
        logger.info(f"Number of chunks: {num_chunks}")
        
        # Calculate file hash for verification
        file_hash = calculate_file_hash(file_path)
        logger.info(f"File hash (SHA-256): {file_hash}")
        
        # Prepare common metadata
        model_id = file_path.stem
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        transfer_id = f"{model_id}-{timestamp}-{file_hash[:8]}"
        logger.info(f"Transfer ID: {transfer_id}")
        
        # First, send a metadata message
        metadata_message = {
            "model_id": model_id,
            "timestamp": timestamp,
            "transfer_id": transfer_id,
            "filename": file_path.name,
            "content_type": "model/gltf-binary",
            "file_size": file_size,
            "chunk_size": chunk_size,
            "num_chunks": num_chunks,
            "hash": file_hash,
            "type": "metadata"
        }
        
        metadata_key = f"{transfer_id}-metadata".encode('utf-8')
        logger.info(f"Sending metadata to topic: {TOPIC}")
        
        metadata_future = producer.send(
            TOPIC,
            key=metadata_key,
            value=metadata_message,
            headers=[
                ('content-type', b'application/json'),
                ('model-id', model_id.encode('utf-8')),
                ('message-type', b'metadata'),
                ('transfer-id', transfer_id.encode('utf-8'))
            ]
        )
        
        metadata_result = metadata_future.get(timeout=10)
        logger.info(f"✅ Metadata sent to partition {metadata_result.partition} at offset {metadata_result.offset}")
        
        # Now send the file chunks
        with open(file_path, 'rb') as f:
            for chunk_index in range(num_chunks):
                # Read a chunk
                chunk_data = f.read(chunk_size)
                
                # Encode chunk as base64
                b64_chunk = base64.b64encode(chunk_data).decode('utf-8')
                
                # Create chunk message
                chunk_message = {
                    "transfer_id": transfer_id,
                    "chunk_index": chunk_index,
                    "total_chunks": num_chunks,
                    "chunk_size": len(chunk_data),
                    "data": b64_chunk,
                    "type": "chunk"
                }
                
                # Create unique key for this chunk
                chunk_key = f"{transfer_id}-chunk-{chunk_index:04d}".encode('utf-8')
                
                # Send chunk
                logger.info(f"Sending chunk {chunk_index+1}/{num_chunks} (size: {len(chunk_data)} bytes)")
                
                chunk_future = producer.send(
                    TOPIC,
                    key=chunk_key,
                    value=chunk_message,
                    headers=[
                        ('content-type', b'application/json'),
                        ('model-id', model_id.encode('utf-8')),
                        ('message-type', b'chunk'),
                        ('transfer-id', transfer_id.encode('utf-8')),
                        ('chunk-index', str(chunk_index).encode('utf-8'))
                    ]
                )
                
                # Get result and occasionally flush to avoid buffering too many messages
                chunk_result = chunk_future.get(timeout=30)
                
                if chunk_index % 5 == 0:
                    producer.flush()
                    logger.info(f"Flushed after chunk {chunk_index+1}")
                
                # Add a small delay between chunks to avoid throttling
                logger.info(f"Waiting 1 second before sending next chunk...")
                time.sleep(1)
        
        # Send a final message to indicate completion
        final_message = {
            "transfer_id": transfer_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "complete",
            "num_chunks_sent": num_chunks,
            "file_size": file_size,
            "hash": file_hash,
            "type": "completion"
        }
        
        final_key = f"{transfer_id}-complete".encode('utf-8')
        logger.info(f"Sending completion message")
        
        final_future = producer.send(
            TOPIC,
            key=final_key,
            value=final_message,
            headers=[
                ('content-type', b'application/json'),
                ('model-id', model_id.encode('utf-8')),
                ('message-type', b'completion'),
                ('transfer-id', transfer_id.encode('utf-8'))
            ]
        )
        
        final_result = final_future.get(timeout=10)
        logger.info(f"✅ Completion message sent to partition {final_result.partition} at offset {final_result.offset}")
        
        # Flush and close producer
        producer.flush()
        producer.close()
        
        logger.info(f"✅ Successfully uploaded GLB file '{file_path.name}' to Redpanda in {num_chunks} chunks")
        logger.info(f"Transfer ID: {transfer_id}")
        
    except Exception as e:
        logger.error(f"Error uploading GLB file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        # Check if a custom chunk size is specified
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            chunk_size = int(sys.argv[2]) * 1024  # Convert KB to bytes
            upload_glb_file_chunked(sys.argv[1], chunk_size)
        else:
            upload_glb_file_chunked(sys.argv[1])
    else:
        # Use default file
        upload_glb_file_chunked() 