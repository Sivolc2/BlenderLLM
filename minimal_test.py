#!/usr/bin/env python3
"""
Minimal Redpanda Auth Test
-------------------------
Tests Redpanda Cloud authentication with a minimal message.
"""

import os
import sys
import json
import logging
import argparse
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MinimalTest")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Test Redpanda Authentication")
    parser.add_argument("--bootstrap_servers", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS"),
                      help="Redpanda Cloud bootstrap servers")
    parser.add_argument("--username", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_USERNAME", "backend"),
                      help="Redpanda Cloud username")
    parser.add_argument("--password", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_PASSWORD"),
                      help="Redpanda Cloud password")
    parser.add_argument("--topic", type=str, default="geojson-data",
                      help="Redpanda topic")
    parser.add_argument("--sasl_mechanism", type=str, default="SCRAM-SHA-256",
                      help="SASL mechanism (PLAIN, SCRAM-SHA-256)")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("kafka").setLevel(logging.DEBUG)
    
    # Validate required parameters
    if not args.bootstrap_servers:
        logger.error("Bootstrap servers not provided")
        sys.exit(1)
    
    if not args.username:
        logger.error("Username not provided")
        sys.exit(1)
    
    if not args.password:
        logger.error("Password not provided")
        sys.exit(1)
    
    # Print connection info
    logger.info(f"Testing connection to: {args.bootstrap_servers}")
    logger.info(f"Using auth mechanism: {args.sasl_mechanism}")
    logger.info(f"Username: {args.username}")
    
    try:
        # Create Kafka producer
        logger.info("Creating Kafka producer...")
        producer_config = {
            "bootstrap_servers": args.bootstrap_servers,
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": args.sasl_mechanism,
            "sasl_plain_username": args.username,
            "sasl_plain_password": args.password,
        }
        
        # Show config (without password)
        safe_config = producer_config.copy()
        safe_config["sasl_plain_password"] = "********"
        logger.info(f"Producer config: {json.dumps(safe_config, indent=2)}")
        
        producer = KafkaProducer(**producer_config)
        logger.info("✅ Connected successfully!")
        
        # Send a simple text message
        test_message = json.dumps({"test": "Simple auth test", "timestamp": "now"}).encode('utf-8')
        logger.info(f"Sending test message to topic {args.topic}")
        
        future = producer.send(args.topic, test_message)
        metadata = future.get(timeout=10)
        logger.info(f"✅ Message delivered to {metadata.topic}, partition {metadata.partition}, offset {metadata.offset}")
        
        producer.flush()
        logger.info("Test completed successfully!")
        
    except KafkaError as e:
        logger.error(f"Kafka error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 