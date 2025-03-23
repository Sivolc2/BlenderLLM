#!/usr/bin/env python3
"""
Redpanda URL Exporter
--------------------
Export references to 3D model files to Redpanda Cloud.
Instead of sending the entire GLB file, this sends a small message with the URL.
"""

import os
import sys
import json
import argparse
import logging
import signal
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError
from uuid import uuid4
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RedpandaExporter")

# Set a timeout handler to prevent hanging
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Export 3D model URLs to Redpanda Cloud")
    parser.add_argument("--model_id", type=str, required=True,
                      help="MasterpieceX model ID")
    parser.add_argument("--model_name", type=str, default=None,
                      help="Model name (defaults to model_id)")
    parser.add_argument("--topic", type=str, default=os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "geojson-data"),
                      help="Redpanda topic to publish to")
    parser.add_argument("--bootstrap_servers", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS"),
                      help="Redpanda Cloud bootstrap servers")
    parser.add_argument("--username", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_USERNAME", "backend"),
                      help="Redpanda Cloud username")
    parser.add_argument("--password", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_PASSWORD", "jQZzu9x3z0WKsjWLmE9ZLf44fKoXag"),
                      help="Redpanda Cloud password")
    parser.add_argument("--sasl_mechanism", type=str, default="SCRAM-SHA-256",
                      help="SASL mechanism (SCRAM-SHA-256, SCRAM-SHA-512)")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    parser.add_argument("--timeout", type=int, default=30,
                      help="Timeout in seconds for operations that might hang (default: 30)")
    return parser.parse_args()

def on_success(metadata):
    """Callback for successful message delivery"""
    logger.info(f"✓ Message delivered to topic '{metadata.topic}' at partition {metadata.partition}, offset {metadata.offset}")

def on_error(e):
    """Callback for message delivery errors"""
    logger.error(f"Error sending message: {e}")

def main():
    args = parse_arguments()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Validate required parameters
    if not args.bootstrap_servers:
        logger.error("Bootstrap servers not provided. Set REDPANDA_CLOUD_BOOTSTRAP_SERVERS environment variable or use --bootstrap_servers")
        sys.exit(1)
    
    if not args.username:
        logger.error("Username not provided. Set REDPANDA_CLOUD_USERNAME environment variable or use --username")
        sys.exit(1)
    
    if not args.password:
        logger.error("Password not provided. Set REDPANDA_CLOUD_PASSWORD environment variable or use --password")
        sys.exit(1)
    
    # Set model ID and name
    model_id = args.model_id
    model_name = args.model_name or model_id
    
    logger.info(f"Exporting model URL: {model_name} (ID: {model_id})")
    
    # Create URLs to the model
    model_dashboard_url = f"https://app.masterpiecex.com/generate/history/{model_id}"
    model_api_url = f"https://api.masterpiecex.com/v3/generation/result/{model_id}"
    model_download_url = f"https://api.masterpiecex.com/v1/model/download/{model_id}"
    
    # Create message payload
    timestamp = datetime.utcnow().isoformat()
    message_id = str(uuid4())
    
    # Create a minimal message with just the URL reference
    message = {
        'id': message_id,
        'timestamp': timestamp,
        'model_id': model_id,
        'model_name': model_name,
        'file_type': 'glb',
        'dashboard_url': model_dashboard_url,
        'api_url': model_api_url,
        'download_url': model_download_url,
        'source': 'masterpiecex',
        'content_type': '3d_model_reference'
    }
    
    # Convert message to JSON
    message_json = json.dumps(message).encode('utf-8')
    message_size = len(message_json)
    logger.info(f"Message size: {message_size} bytes")
    
    try:
        # Set timeout for the entire operation
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.timeout)
        
        logger.info(f"Connecting to Redpanda Cloud at {args.bootstrap_servers}")
        producer = KafkaProducer(
            bootstrap_servers=args.bootstrap_servers,
            security_protocol="SASL_SSL",
            sasl_mechanism=args.sasl_mechanism,
            sasl_plain_username=args.username,
            sasl_plain_password=args.password,
            compression_type="gzip"  # Use compression to reduce message size
        )
        
        # Reset alarm after successful connection
        signal.alarm(0)
        logger.info("Connected successfully!")
        
        # Send the message
        signal.alarm(args.timeout)
        logger.info(f"Sending message to topic {args.topic}")
        future = producer.send(
            args.topic,
            key=model_id.encode('utf-8'),
            value=message_json,
            headers=[
                ('content-type', b'application/json'),
                ('model-id', model_id.encode('utf-8')),
                ('model-name', model_name.encode('utf-8'))
            ]
        )
        future.add_callback(on_success)
        future.add_errback(on_error)
        
        # Reset alarm after sending
        signal.alarm(0)
        
        # Flush to ensure delivery
        signal.alarm(args.timeout)
        logger.info("Flushing message...")
        remaining = producer.flush(timeout=args.timeout)
        
        # Verify message was delivered
        if remaining > 0:
            logger.error(f"Failed to deliver message before timeout")
            sys.exit(1)
            
        # Check future to make sure it completed
        try:
            metadata = future.get(timeout=1.0)
            logger.info(f"✅ Message confirmed delivered to partition {metadata.partition} at offset {metadata.offset}")
        except Exception as e:
            logger.error(f"Message delivery verification failed: {e}")
            sys.exit(1)
        
        logger.info(f"✅ Successfully exported model URL '{model_name}' to Redpanda Cloud topic {args.topic}")
        logger.info(f"To view in Redpanda UI, look for message with key: {model_id}")
        
    except TimeoutError:
        logger.error(f"Operation timed out after {args.timeout} seconds")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation canceled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error exporting to Redpanda: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Always reset the alarm when done
        signal.alarm(0)

if __name__ == "__main__":
    main() 