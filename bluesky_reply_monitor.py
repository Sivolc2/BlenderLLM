#!/usr/bin/env python3
"""
Bluesky Reply Monitor
--------------------
Monitors replies to a specific Bluesky post and sends notifications to Redpanda
when new replies are detected.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

# Bluesky API client
from atproto import Client as BlueskyClient
# Kafka client for Redpanda
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlueskyReplyMonitor")

class BlueskyReplyMonitor:
    """
    Monitor for replies to a specific Bluesky post with Redpanda integration.
    Follows the Single Responsibility Principle by separating concerns:
    - Bluesky API interactions
    - Reply tracking
    - Redpanda notifications
    """
    
    def __init__(self, 
                 post_uri: str, 
                 poll_interval: int = 60,
                 redpanda_config: Optional[Dict[str, Any]] = None,
                 redpanda_topic: str = "bluesky-replies"):
        """
        Initialize the monitor.
        
        Args:
            post_uri: URI of the Bluesky post to monitor
            poll_interval: Time in seconds between checking for new replies
            redpanda_config: Configuration for Redpanda connection
            redpanda_topic: Redpanda topic to send notifications to
        """
        self.post_uri = post_uri
        self.poll_interval = poll_interval
        self.redpanda_topic = redpanda_topic
        self.redpanda_config = redpanda_config or {}
        
        self.bsky_client = None
        self.producer = None
        self.known_replies: Set[str] = set()  # URIs of replies we've seen
        self.post_details = None  # Will store details about the original post
        
        # State tracking
        self.running = False
        self.last_check_time = None
    
    def setup_bluesky_client(self, handle: str, password: str) -> None:
        """
        Initialize and authenticate the Bluesky client.
        
        Args:
            handle: Bluesky handle (username)
            password: Bluesky app password
        """
        try:
            self.bsky_client = BlueskyClient()
            self.bsky_client.login(handle, password)
            logger.info(f"Successfully logged in to Bluesky as {handle}")
            
            # Get details about the post we're monitoring
            self._fetch_post_details()
        except Exception as e:
            logger.error(f"Failed to log in to Bluesky: {e}")
            raise
    
    def setup_redpanda(self) -> None:
        """Initialize the Redpanda producer"""
        if not self.redpanda_config:
            logger.warning("No Redpanda configuration provided, messages will not be sent")
            return
            
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.redpanda_config.get("bootstrap_servers", "localhost:9092"),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                **{k: v for k, v in self.redpanda_config.items() 
                   if k not in ["bootstrap_servers"]}
            )
            logger.info(f"Connected to Redpanda at {self.redpanda_config.get('bootstrap_servers')}")
        except Exception as e:
            logger.error(f"Failed to connect to Redpanda: {e}")
            self.producer = None
    
    def _fetch_post_details(self) -> None:
        """Fetch details about the post we're monitoring"""
        if not self.bsky_client:
            raise ValueError("Bluesky client not initialized")
            
        # Parse URI to get the necessary components
        parts = self.post_uri.split('/')
        if len(parts) < 5:
            raise ValueError(f"Invalid post URI format: {self.post_uri}")
            
        # The URI format is like: at://did:plc:xyz/app.bsky.feed.post/timestamp
        repo = parts[2]  # The DID
        rkey = parts[4]  # The post ID
        
        # Get the post using getRecord
        try:
            post_data = self.bsky_client.app.bsky.feed.get_post_thread({
                "uri": self.post_uri
            })
            
            self.post_details = post_data.thread.post
            author = self.post_details.author.display_name or self.post_details.author.handle
            
            logger.info(f"Monitoring post by {author}: \"{self.post_details.record.text[:100]}...\"")
        except Exception as e:
            logger.error(f"Failed to get post details: {e}")
            raise
    
    def send_to_redpanda(self, reply_data: Dict[str, Any]) -> bool:
        """
        Send a notification about a new reply to Redpanda.
        
        Args:
            reply_data: Data about the reply to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.producer:
            logger.warning("Redpanda producer not initialized, message not sent")
            return False
            
        try:
            # Create a message with the reply data and metadata
            message = {
                "event_type": "new_reply",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "post_uri": self.post_uri,
                "reply": reply_data
            }
            
            # Send to Redpanda
            future = self.producer.send(
                self.redpanda_topic,
                key=reply_data.get("uri", "unknown"),
                value=message
            )
            
            # Wait for the result to ensure delivery
            result = future.get(timeout=10)
            logger.info(f"Reply notification sent to Redpanda: partition={result.partition}, offset={result.offset}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to Redpanda: {e}")
            return False
    
    def check_for_new_replies(self) -> List[Dict[str, Any]]:
        """
        Check for new replies to the monitored post.
        
        Returns:
            List of new replies found
        """
        if not self.bsky_client or not self.post_details:
            raise ValueError("Bluesky client or post details not initialized")
            
        try:
            # Get the post thread which includes replies
            thread_data = self.bsky_client.app.bsky.feed.get_post_thread({
                "uri": self.post_uri,
                "depth": 1  # Only get direct replies
            })
            
            # Extract replies from the thread
            replies = []
            if hasattr(thread_data.thread, "replies") and thread_data.thread.replies:
                for reply in thread_data.thread.replies:
                    reply_uri = reply.post.uri
                    
                    # Check if we've seen this reply before
                    if reply_uri not in self.known_replies:
                        # This is a new reply
                        reply_data = {
                            "uri": reply_uri,
                            "author": {
                                "did": reply.post.author.did,
                                "handle": reply.post.author.handle,
                                "display_name": reply.post.author.display_name
                            },
                            "text": reply.post.record.text,
                            "created_at": reply.post.record.created_at
                        }
                        
                        # Add to our known replies set
                        self.known_replies.add(reply_uri)
                        replies.append(reply_data)
            
            # Log the number of new replies found
            if replies:
                logger.info(f"Found {len(replies)} new replies")
            
            return replies
                
        except Exception as e:
            logger.error(f"Error checking for replies: {e}")
            return []
    
    def start_monitoring(self) -> None:
        """Start the monitoring loop"""
        if not self.bsky_client:
            raise ValueError("Bluesky client not initialized")
            
        logger.info(f"Starting reply monitoring for post {self.post_uri}")
        logger.info(f"Poll interval: {self.poll_interval} seconds")
        
        self.running = True
        
        # Initial check to populate known replies
        initial_replies = self.check_for_new_replies()
        logger.info(f"Found {len(initial_replies)} existing replies, these will be ignored")
        
        try:
            while self.running:
                self.last_check_time = datetime.now(timezone.utc)
                
                # Check for new replies
                new_replies = self.check_for_new_replies()
                
                # Process any new replies
                for reply in new_replies:
                    logger.info(f"New reply from {reply['author']['handle']}: {reply['text'][:100]}...")
                    
                    # Send notification to Redpanda
                    self.send_to_redpanda(reply)
                
                # Wait for the next poll interval
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.running = False
            
            # Close connections
            if self.producer:
                self.producer.flush()  # Ensure all messages are sent
                self.producer.close()
                logger.info("Redpanda producer closed")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Bluesky Reply Monitor")
    
    # Bluesky configuration
    parser.add_argument("--post-uri", type=str, required=True,
                      help="URI of the Bluesky post to monitor")
    parser.add_argument("--handle", type=str,
                      default=os.environ.get("BLUESKY_HANDLE"),
                      help="Bluesky handle/username")
    parser.add_argument("--password", type=str,
                      default=os.environ.get("BLUESKY_APP_PASSWORD"),
                      help="Bluesky app password")
    
    # Monitoring settings
    parser.add_argument("--poll-interval", type=int, default=60,
                      help="Time in seconds between checks for new replies")
    
    # Redpanda configuration
    parser.add_argument("--redpanda-servers", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_BOOTSTRAP_SERVERS", "localhost:9092"),
                      help="Redpanda bootstrap servers")
    parser.add_argument("--redpanda-topic", type=str, default="bluesky-replies",
                      help="Redpanda topic to send notifications to")
    parser.add_argument("--redpanda-username", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_USERNAME"),
                      help="Redpanda SASL username")
    parser.add_argument("--redpanda-password", type=str,
                      default=os.environ.get("REDPANDA_CLOUD_PASSWORD"),
                      help="Redpanda SASL password")
    
    # Other settings
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # Set up logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("atproto").setLevel(logging.DEBUG)
        logging.getLogger("kafka").setLevel(logging.DEBUG)
    
    # Validate required arguments
    if not args.handle or not args.password:
        logger.error("Bluesky handle and password are required")
        logger.info("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables or use --handle and --password")
        return 1
        
    # Create the Redpanda configuration
    redpanda_config = {
        "bootstrap_servers": args.redpanda_servers
    }
    
    # Add authentication if provided
    if args.redpanda_username and args.redpanda_password:
        redpanda_config.update({
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": "SCRAM-SHA-256",
            "sasl_plain_username": args.redpanda_username,
            "sasl_plain_password": args.redpanda_password
        })
    
    try:
        # Create and set up the monitor
        monitor = BlueskyReplyMonitor(
            post_uri=args.post_uri,
            poll_interval=args.poll_interval,
            redpanda_config=redpanda_config,
            redpanda_topic=args.redpanda_topic
        )
        
        # Set up connections
        monitor.setup_bluesky_client(args.handle, args.password)
        monitor.setup_redpanda()
        
        # Start monitoring
        monitor.start_monitoring()
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 