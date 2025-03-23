#!/usr/bin/env python3
"""
Bluesky Monitor - Main Entry Point
--------------------------------
A unified script that activates both Redpanda and Bluesky watch functionality
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional

from bsky_monitor.modules import ReplyMonitor, web_url_to_at_uri

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bsky_monitor")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Bluesky Post Monitor with Redpanda Integration")
    
    # Post identifier (URL or URI)
    post_group = parser.add_mutually_exclusive_group(required=True)
    post_group.add_argument("--post-url", type=str,
                      help="Bluesky post URL (e.g., https://bsky.app/profile/handle.bsky.social/post/xyz)")
    post_group.add_argument("--post-uri", type=str,
                      help="AT Protocol URI of the post to monitor")
    
    # Bluesky authentication
    parser.add_argument("--handle", type=str,
                      default=os.environ.get("BLUESKY_HANDLE"),
                      help="Bluesky handle/username")
    parser.add_argument("--password", type=str,
                      default=os.environ.get("BLUESKY_APP_PASSWORD"),
                      help="Bluesky app password")
    
    # Monitoring settings
    parser.add_argument("--poll-interval", type=int, default=5,
                      help="Time in seconds between checks for new replies (default: 5)")
    
    # Redpanda settings
    parser.add_argument("--redpanda-servers", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", "localhost:9092"),
                      help="Redpanda bootstrap servers")
    parser.add_argument("--redpanda-topic", type=str, 
                      default=os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "bluesky-replies"),
                      help="Redpanda topic for notifications")
    parser.add_argument("--redpanda-username", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_USERNAME"),
                      help="Redpanda SASL username")
    parser.add_argument("--redpanda-password", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_PASSWORD"),
                      help="Redpanda SASL password")
    parser.add_argument("--no-redpanda", action="store_true",
                      help="Skip Redpanda integration (monitoring only)")
    
    # Debugging
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    
    return parser.parse_args()

def create_redpanda_config(args) -> Optional[Dict[str, Any]]:
    """
    Create Redpanda configuration from arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Configuration dictionary or None if Redpanda is disabled
    """
    if args.no_redpanda:
        return None
        
    config = {
        "bootstrap_servers": args.redpanda_servers
    }
    
    # Add authentication if provided
    if args.redpanda_username and args.redpanda_password:
        config.update({
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": "SCRAM-SHA-256",
            "sasl_plain_username": args.redpanda_username,
            "sasl_plain_password": args.redpanda_password
        })
    
    return config

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Set up logging
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("bsky_monitor.modules").setLevel(logging.DEBUG)
        logging.getLogger("kafka").setLevel(logging.DEBUG)
    
    # Validate required arguments
    if not args.handle or not args.password:
        logger.error("Bluesky handle and password are required")
        logger.info("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables or use --handle and --password")
        return 1
    
    # Get post URI (convert URL if needed)
    post_uri = args.post_uri
    if args.post_url:
        logger.info(f"Converting post URL: {args.post_url}")
        post_uri = web_url_to_at_uri(args.post_url)
        if not post_uri:
            logger.error("Failed to convert post URL to AT URI")
            return 1
        logger.info(f"Post URI: {post_uri}")
    
    # Create Redpanda configuration
    redpanda_config = create_redpanda_config(args)
    if args.no_redpanda:
        logger.info("Redpanda integration disabled")
    
    try:
        # Create and set up the monitor
        monitor = ReplyMonitor(
            post_uri=post_uri,
            poll_interval=args.poll_interval,
            redpanda_topic=args.redpanda_topic
        )
        
        # Authenticate with Bluesky
        logger.info(f"Authenticating with Bluesky as {args.handle}")
        if not monitor.authenticate_bluesky(args.handle, args.password):
            logger.error("Failed to authenticate with Bluesky")
            return 1
        
        # Connect to Redpanda if enabled
        if redpanda_config:
            logger.info(f"Connecting to Redpanda at {args.redpanda_servers}")
            if not monitor.connect_redpanda(redpanda_config):
                logger.warning("Failed to connect to Redpanda, continuing with monitoring only")
        
        # Start monitoring
        monitor.start_monitoring()
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 