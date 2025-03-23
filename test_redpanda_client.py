#!/usr/bin/env python3
"""
Test RedpandaClient Module
--------------------------
Tests the RedpandaClient module from the bsky_monitor package.
"""

import os
import sys
import logging
import time

from bsky_monitor.modules.redpanda_client import RedpandaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RedpandaClientTest")

# Redpanda connection settings from environment variables
BOOTSTRAP_SERVERS = os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", 
                                 "cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092")
USERNAME = os.environ.get("REDPANDA_CLOUD_USERNAME", "backend")
PASSWORD = os.environ.get("REDPANDA_CLOUD_PASSWORD", "jQZzu9x3z0WKsjWLmE9ZLf44fKoXag")
TOPIC = os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "geojson-data")

def create_redpanda_config():
    """Create configuration for Redpanda connection"""
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

def test_redpanda_client():
    """Test the RedpandaClient from the bsky_monitor package"""
    
    # Create the client
    client = RedpandaClient()
    
    try:
        # Get configuration
        config = create_redpanda_config()
        
        # Connect as producer
        logger.info("Connecting to Redpanda as producer...")
        if not client.connect_producer(config):
            logger.error("Failed to connect to Redpanda as producer")
            return False
        
        # Send a test message
        test_message = {
            "test": "message",
            "source": "redpanda_client_test",
            "timestamp": time.time(),
            "content": "This is a test message from the RedpandaClient test"
        }
        
        logger.info(f"Sending test message to topic: {TOPIC}")
        success = client.send_message(
            TOPIC,
            key="test-message-from-client",
            value=test_message
        )
        
        if not success:
            logger.error("Failed to send message")
            return False
            
        logger.info("Message sent successfully")
        
        # Close the client
        client.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing RedpandaClient: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=== STARTING REDPANDA CLIENT TEST ===")
    
    success = test_redpanda_client()
    
    if success:
        logger.info("=== REDPANDA CLIENT TEST COMPLETED SUCCESSFULLY ===")
        sys.exit(0)
    else:
        logger.error("=== REDPANDA CLIENT TEST FAILED ===")
        sys.exit(1) 