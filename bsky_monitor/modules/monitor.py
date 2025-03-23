"""
Reply Monitor Module
-----------------
Core monitoring functionality for tracking Bluesky post replies
"""

import os
import time
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime, timezone

from bsky_monitor.modules.bluesky_client import BlueskyClient
from bsky_monitor.modules.redpanda_client import RedpandaClient

logger = logging.getLogger(__name__)

class ReplyMonitor:
    """
    Monitor for replies to a specific Bluesky post with Redpanda integration.
    Core monitoring functionality that coordinates the Bluesky and Redpanda clients.
    """
    
    def __init__(self, 
                 post_uri: str, 
                 poll_interval: int = 5,
                 redpanda_topic: str = None):
        """
        Initialize the monitor.
        
        Args:
            post_uri: URI of the Bluesky post to monitor
            poll_interval: Time in seconds between checking for new replies
            redpanda_topic: Redpanda topic to send notifications to
        """
        self.post_uri = post_uri
        self.poll_interval = poll_interval
        # Use environment variable if available, otherwise default to "bluesky-replies"
        self.redpanda_topic = redpanda_topic or os.environ.get("REDPANDA_CLOUD_GEOJSON_TOPIC", "bluesky-replies")
        
        self.bsky_client = BlueskyClient()
        self.redpanda_client = RedpandaClient()
        
        self.known_replies: Set[str] = set()  # URIs of replies we've seen
        self.post_details = None  # Will store details about the original post
        
        # State tracking
        self.running = False
        self.last_check_time = None
        
        logger.debug(f"ReplyMonitor initialized with topic: {self.redpanda_topic}")
    
    def authenticate_bluesky(self, handle: str, password: str) -> bool:
        """
        Authenticate with Bluesky.
        
        Args:
            handle: Bluesky handle/username
            password: Bluesky app password
            
        Returns:
            bool: True if authentication was successful
        """
        success = self.bsky_client.login(handle, password)
        if success:
            # Get details about the post we're monitoring
            self.post_details = self.bsky_client.get_post_details(self.post_uri)
            if self.post_details:
                author = self.post_details["author"]["handle"]
                logger.info(f"Monitoring post by {author}: \"{self.post_details['text'][:100]}...\"")
            return True
        return False
    
    def connect_redpanda(self, config: Dict[str, Any]) -> bool:
        """
        Connect to Redpanda.
        
        Args:
            config: Configuration dictionary for Redpanda connection
            
        Returns:
            bool: True if connection was successful
        """
        return self.redpanda_client.connect_producer(config)
    
    def check_for_new_replies(self) -> List[Dict[str, Any]]:
        """
        Check for new replies to the monitored post.
        
        Returns:
            List of new replies found
        """
        # Get all replies to the post
        all_replies = self.bsky_client.get_post_replies(self.post_uri)
        
        # Filter out replies we've already seen
        new_replies = []
        for reply in all_replies:
            reply_uri = reply["uri"]
            if reply_uri not in self.known_replies:
                self.known_replies.add(reply_uri)
                new_replies.append(reply)
        
        if new_replies:
            logger.info(f"Found {len(new_replies)} new replies")
        
        return new_replies
    
    def process_reply(self, reply: Dict[str, Any]) -> bool:
        """
        Process a new reply.
        
        Args:
            reply: Reply data dictionary
            
        Returns:
            bool: True if processing was successful
        """
        # Log the new reply
        author_handle = reply["author"]["handle"]
        logger.info(f"New reply from {author_handle}: {reply['text'][:100]}...")
        
        # Send to Redpanda if connected
        if self.redpanda_client.connected:
            message = {
                "event_type": "new_reply",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "post_uri": self.post_uri,
                "reply": reply
            }
            
            logger.debug(f"Sending message to Redpanda topic: {self.redpanda_topic}")
            return self.redpanda_client.send_message(
                self.redpanda_topic,
                key=reply["uri"],
                value=message
            )
        else:
            logger.warning("Redpanda not connected, message not sent")
            return False
    
    def start_monitoring(self) -> None:
        """Start the monitoring loop."""
        if not self.bsky_client.authenticated:
            logger.error("Bluesky client not authenticated")
            return
            
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
                    self.process_reply(reply)
                
                # Wait for the next poll interval
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring loop and clean up resources."""
        self.running = False
        self.redpanda_client.close()
        logger.info("Monitoring stopped") 