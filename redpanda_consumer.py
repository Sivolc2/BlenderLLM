#!/usr/bin/env python3
"""
Redpanda Consumer Script
------------------------
A simple script to consume messages from a Redpanda topic
and display them in the console.
"""

import os
import json
import logging
import argparse
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("redpanda_consumer")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Redpanda Consumer")
    
    # Redpanda settings
    parser.add_argument("--bootstrap-servers", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", "localhost:9092"),
                      help="Redpanda bootstrap servers")
    parser.add_argument("--topic", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "geojson-data"),
                      help="Redpanda topic to consume from")
    parser.add_argument("--username", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_USERNAME"),
                      help="Redpanda SASL username")
    parser.add_argument("--password", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_PASSWORD"),
                      help="Redpanda SASL password")
    parser.add_argument("--group-id", type=str,
                      default="bsky-consumer",
                      help="Consumer group ID")
    
    # Other options
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    
    return parser.parse_args()

def create_consumer(args):
    """Create a Kafka consumer with the provided arguments"""
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("kafka").setLevel(logging.DEBUG)
    
    # Create consumer configuration
    config = {
        "bootstrap_servers": args.bootstrap_servers,
        "group_id": args.group_id,
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
        "value_deserializer": lambda m: json.loads(m.decode('utf-8')),
        "key_deserializer": lambda m: m.decode('utf-8') if m else None,
        "reconnect_backoff_ms": 1000,
        "reconnect_backoff_max_ms": 10000,
        "request_timeout_ms": 30000,
        "retry_backoff_ms": 500,
    }
    
    # Add authentication if provided
    if args.username and args.password:
        config.update({
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": "SCRAM-SHA-256",
            "sasl_plain_username": args.username,
            "sasl_plain_password": args.password
        })
    
    try:
        logger.info(f"Connecting to Redpanda at {args.bootstrap_servers}")
        logger.info(f"Consuming from topic: {args.topic}")
        
        consumer = KafkaConsumer(
            args.topic,
            **config
        )
        return consumer
    except Exception as e:
        logger.error(f"Failed to create consumer: {e}")
        return None

def process_message(key, value):
    """Process a received message"""
    event_type = value.get("event_type", "unknown")
    timestamp = value.get("timestamp", "unknown")
    
    if event_type == "new_reply":
        reply = value.get("reply", {})
        author = reply.get("author", {}).get("handle", "unknown")
        text = reply.get("text", "")[:100]
        
        logger.info(f"New reply from {author}: {text}...")
        logger.debug(f"Full message: {json.dumps(value, indent=2)}")
    else:
        logger.info(f"Received message of type {event_type} at {timestamp}")
        logger.debug(f"Full message: {json.dumps(value, indent=2)}")

def main():
    """Main entry point"""
    args = parse_arguments()
    
    consumer = create_consumer(args)
    if not consumer:
        return 1
    
    try:
        logger.info("Starting consumer, waiting for messages...")
        
        while True:
            # Poll for messages
            message_batch = consumer.poll(timeout_ms=1000)
            
            if not message_batch:
                # No messages received in this poll
                logger.debug("No messages received, polling again...")
                time.sleep(1)
                continue
            
            for topic_partition, messages in message_batch.items():
                for message in messages:
                    logger.debug(f"Received message: topic={topic_partition.topic}, "
                                f"partition={topic_partition.partition}, "
                                f"offset={message.offset}, key={message.key}")
                    
                    # Process the message
                    try:
                        process_message(message.key, message.value)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
    
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Error in consumer: {e}")
    finally:
        if consumer:
            consumer.close()
            logger.info("Consumer closed")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 