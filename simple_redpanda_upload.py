#!/usr/bin/env python3
"""
Simple Redpanda File Upload
---------------------------
A minimal script to upload a text file to Redpanda and confirm it was sent.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RedpandaUpload")

# Redpanda connection settings - using values from export_model_url.sh
BOOTSTRAP_SERVERS = os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", 
                                 "cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092")
USERNAME = os.environ.get("REDPANDA_CLOUD_USERNAME", "backend")
PASSWORD = os.environ.get("REDPANDA_CLOUD_PASSWORD", "jQZzu9x3z0WKsjWLmE9ZLf44fKoXag")
TOPIC = os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "geojson-data")
INPUT_FILE = "simple_test.txt"

def get_kafka_config():
    """Create Kafka configuration"""
    config = {
        "bootstrap_servers": BOOTSTRAP_SERVERS,
        "security_protocol": "SASL_SSL",
        "sasl_mechanism": "SCRAM-SHA-256",
        "sasl_plain_username": USERNAME,
        "sasl_plain_password": PASSWORD
    }
    return config

def upload_file():
    """Upload a file to Redpanda topic and confirm it was sent"""
    file_path = Path(INPUT_FILE)
    
    if not file_path.exists():
        logger.error(f"File not found: {INPUT_FILE}")
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
        
        # Read file content
        logger.info(f"Reading file: {INPUT_FILE}")
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Create message with file metadata and timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        message = {
            "filename": file_path.name,
            "content_type": "text/plain",
            "content": content,
            "timestamp": timestamp
        }
        
        # Send message with unique key based on timestamp
        message_key = f"{file_path.name}-{timestamp}".encode('utf-8')
        logger.info(f"Sending file to topic: {TOPIC}")
        
        # Send the message and get the future
        future = producer.send(
            TOPIC,
            key=message_key,
            value=message
        )
        
        # Wait for the message to be sent and get the metadata
        metadata = future.get(timeout=10)
        logger.info(f"✅ File sent to partition {metadata.partition} at offset {metadata.offset}")
        
        # Flush any remaining messages
        producer.flush()
        
        # Return information needed for confirmation
        return {
            "topic": TOPIC,
            "partition": metadata.partition,
            "offset": metadata.offset,
            "key": message_key.decode('utf-8')
        }
            
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def confirm_upload(message_info):
    """Confirm the message was successfully uploaded by consuming it back"""
    try:
        logger.info("Confirming message was uploaded by consuming it back...")
        
        # Create consumer config
        consumer_config = get_kafka_config()
        consumer_config.update({
            "group_id": f"confirmation-group-{int(time.time())}",  # Unique group ID
            "auto_offset_reset": "earliest",
            "consumer_timeout_ms": 10000,  # 10 seconds timeout
            "value_deserializer": lambda m: json.loads(m.decode('utf-8')),
            "key_deserializer": lambda m: m.decode('utf-8') if m else None
        })
        
        # Create consumer and assign to specific partition/offset
        consumer = KafkaConsumer(**consumer_config)
        
        # Assign to specific partition and offset
        from kafka.structs import TopicPartition
        tp = TopicPartition(message_info["topic"], message_info["partition"])
        consumer.assign([tp])
        consumer.seek(tp, message_info["offset"])
        
        # Try to consume the message
        logger.info(f"Looking for message at partition {message_info['partition']}, offset {message_info['offset']}")
        
        found = False
        for message in consumer:
            if message.key == message_info["key"]:
                logger.info("✅ MESSAGE CONFIRMED! Successfully retrieved the uploaded message:")
                logger.info(f"Key: {message.key}")
                logger.info(f"Timestamp: {message.value.get('timestamp')}")
                
                # Print preview of content
                content = message.value.get('content', '')
                preview = content[:50] + "..." if len(content) > 50 else content
                logger.info(f"Content preview: {preview}")
                
                found = True
                break
        
        if not found:
            logger.error("❌ Could not confirm message was uploaded. It might be there but couldn't be found.")
            
        consumer.close()
        return found
        
    except Exception as e:
        logger.error(f"Error confirming upload: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    logger.info("=== STARTING SIMPLE REDPANDA FILE UPLOAD ===")
    
    # Upload the file
    message_info = upload_file()
    
    # Wait a moment to ensure message is available
    logger.info("Waiting for 2 seconds before confirming...")
    time.sleep(2)
    
    # Confirm the upload
    success = confirm_upload(message_info)
    
    if success:
        logger.info("=== FILE UPLOAD AND CONFIRMATION COMPLETED SUCCESSFULLY ===")
    else:
        logger.info("=== FILE WAS UPLOADED BUT CONFIRMATION FAILED ===")

if __name__ == "__main__":
    main() 