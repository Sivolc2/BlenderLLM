#!/usr/bin/env python3
"""
Simple Redpanda Client
---------------------
A basic producer-consumer example for Redpanda/Kafka using kafka-python.
Demonstrates how to:
1. Upload a text file to a Redpanda topic
2. Consume messages from a Redpanda topic
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RedpandaSimpleClient")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Simple Redpanda Producer-Consumer")
    parser.add_argument("--mode", type=str, choices=["produce", "consume"], required=True,
                      help="Operation mode: produce to upload a file, consume to read messages")
    parser.add_argument("--file", type=str, 
                      help="File to upload (required for produce mode)")
    parser.add_argument("--bootstrap_servers", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", "localhost:9092"),
                      help="Redpanda bootstrap servers")
    parser.add_argument("--topic", type=str, default="test-topic",
                      help="Redpanda topic name")
    parser.add_argument("--username", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_USERNAME"),
                      help="SASL username (if using authentication)")
    parser.add_argument("--password", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_PASSWORD"),
                      help="SASL password (if using authentication)")
    parser.add_argument("--group_id", type=str, default="simple-consumer-group",
                      help="Consumer group ID (for consume mode)")
    parser.add_argument("--sasl_mechanism", type=str, default="SCRAM-SHA-256",
                      help="SASL mechanism (PLAIN, SCRAM-SHA-256)")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    return parser.parse_args()

def get_kafka_config(args):
    """Create Kafka configuration based on arguments"""
    config = {
        "bootstrap_servers": args.bootstrap_servers
    }
    
    # Add authentication if username and password provided
    if args.username and args.password:
        config.update({
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": args.sasl_mechanism,
            "sasl_plain_username": args.username,
            "sasl_plain_password": args.password
        })
        
    return config

def on_success(metadata):
    """Callback for successful message delivery"""
    logger.info(f"✅ Message delivered to {metadata.topic}, partition {metadata.partition}, offset {metadata.offset}")

def on_error(e):
    """Callback for message delivery errors"""
    logger.error(f"❌ Error sending message: {e}")

def produce_file(args, config):
    """Upload a file to Redpanda topic"""
    file_path = Path(args.file)
    
    if not file_path.exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    try:
        # Create producer
        logger.info(f"Connecting to Redpanda at {args.bootstrap_servers}")
        producer = KafkaProducer(**config)
        logger.info("✅ Connected successfully!")
        
        # Read file content
        logger.info(f"Reading file: {args.file}")
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Create message with file metadata
        message = {
            "filename": file_path.name,
            "content_type": "text/plain",
            "content": content
        }
        
        # Serialize message
        message_json = json.dumps(message).encode('utf-8')
        message_size = len(message_json)
        logger.info(f"Message size: {message_size} bytes")
        
        # Send message
        logger.info(f"Sending file to topic: {args.topic}")
        future = producer.send(
            args.topic,
            key=file_path.name.encode('utf-8'),
            value=message_json
        )
        future.add_callback(on_success)
        future.add_errback(on_error)
        
        # Ensure delivery
        producer.flush()
        
        # Check future to make sure it completed
        try:
            metadata = future.get(timeout=10)
            logger.info(f"✅ File successfully sent to partition {metadata.partition} at offset {metadata.offset}")
        except Exception as e:
            logger.error(f"Message delivery verification failed: {e}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in producer: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def consume_messages(args, config):
    """Consume messages from Redpanda topic"""
    try:
        # Add consumer-specific configs
        config.update({
            "group_id": args.group_id,
            "auto_offset_reset": "earliest",  # Start from beginning of topic
            "enable_auto_commit": True,
            "value_deserializer": lambda m: json.loads(m.decode('utf-8')),
            "key_deserializer": lambda m: m.decode('utf-8') if m else None
        })
        
        # Create consumer
        logger.info(f"Connecting consumer to {args.bootstrap_servers}")
        logger.info(f"Subscribing to topic: {args.topic}")
        consumer = KafkaConsumer(args.topic, **config)
        
        # Poll for messages
        logger.info(f"Waiting for messages... (Press Ctrl+C to exit)")
        try:
            for message in consumer:
                logger.info(f"Received message from partition {message.partition}, offset {message.offset}")
                logger.info(f"Key: {message.key}")
                
                # Extract content if it's a file
                if isinstance(message.value, dict) and "filename" in message.value:
                    logger.info(f"Filename: {message.value['filename']}")
                    if "content" in message.value:
                        content_preview = message.value["content"][:100] + "..." if len(message.value["content"]) > 100 else message.value["content"]
                        logger.info(f"Content preview: {content_preview}")
                else:
                    logger.info(f"Value: {message.value}")
                
                logger.info("-" * 50)
                
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user.")
            
    except Exception as e:
        logger.error(f"Error in consumer: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def main():
    args = parse_arguments()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("kafka").setLevel(logging.DEBUG)
    
    # Get Kafka configuration
    config = get_kafka_config(args)
    
    # Execute requested mode
    if args.mode == "produce":
        if not args.file:
            logger.error("--file argument is required for produce mode")
            sys.exit(1)
        produce_file(args, config)
    else:  # consume
        consume_messages(args, config)

if __name__ == "__main__":
    main() 