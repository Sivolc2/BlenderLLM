#!/usr/bin/env python3
"""
Test Redpanda Connection
------------------------
A minimal script to test Redpanda connectivity and send a simple message.
"""

import os
import sys
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RedpandaTest")

# Redpanda connection settings from environment variables
BOOTSTRAP_SERVERS = os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", 
                                  "cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092")
USERNAME = os.environ.get("REDPANDA_CLOUD_USERNAME", "backend")
PASSWORD = os.environ.get("REDPANDA_CLOUD_PASSWORD", "jQZzu9x3z0WKsjWLmE9ZLf44fKoXag")
TOPIC = os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "geojson-data")

def get_kafka_config():
    """Create Kafka configuration"""
    config = {
        "bootstrap_servers": BOOTSTRAP_SERVERS,
        "security_protocol": "SASL_SSL",
        "sasl_mechanism": "SCRAM-SHA-256",
        "sasl_plain_username": USERNAME,
        "sasl_plain_password": PASSWORD
    }
    logger.info(f"Using bootstrap servers: {BOOTSTRAP_SERVERS}")
    logger.info(f"Using username: {USERNAME}")
    logger.info(f"Password is {'set' if PASSWORD else 'not set'}")
    return config

def test_redpanda_connection():
    """Test connection to Redpanda and send a simple message"""
    try:
        # Create producer
        logger.info("Connecting to Redpanda...")
        producer_config = get_kafka_config()
        producer = KafkaProducer(
            **producer_config,
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        logger.info("✅ Connected successfully to Redpanda!")
        
        # Create a simple test message
        message = {
            "test": "message",
            "source": "test_script",
            "content": "This is a test message from the Redpanda test script"
        }
        
        # Send the message
        logger.info(f"Sending test message to topic: {TOPIC}")
        future = producer.send(
            TOPIC,
            key=b"test-message-key",
            value=message
        )
        
        # Wait for the message to be sent and get the metadata
        metadata = future.get(timeout=10)
        logger.info(f"✅ Message sent to partition {metadata.partition} at offset {metadata.offset}")
        
        # Flush and close
        producer.flush()
        producer.close()
        
        return True
            
    except KafkaError as ke:
        logger.error(f"Kafka error: {ke}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        logger.error(f"Error testing Redpanda connection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=== STARTING REDPANDA CONNECTION TEST ===")
    
    success = test_redpanda_connection()
    
    if success:
        logger.info("=== REDPANDA TEST COMPLETED SUCCESSFULLY ===")
        sys.exit(0)
    else:
        logger.error("=== REDPANDA TEST FAILED ===")
        sys.exit(1) 