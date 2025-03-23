"""
Bluesky Client Module
-------------------
Handles interactions with the Bluesky API
"""

import logging
import re
import requests
from typing import Dict, List, Any, Tuple, Optional
from atproto import Client as AtprotoClient

logger = logging.getLogger(__name__)

class BlueskyClient:
    """
    A client for interacting with the Bluesky API.
    Handles authentication, post retrieval, and reply monitoring.
    """
    
    def __init__(self):
        """Initialize the Bluesky client."""
        self.client = None
        self.authenticated = False
    
    def login(self, handle: str, password: str) -> bool:
        """
        Authenticate with Bluesky.
        
        Args:
            handle: Bluesky handle (username)
            password: Bluesky app password
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            self.client = AtprotoClient()
            self.client.login(handle, password)
            self.authenticated = True
            logger.info(f"Successfully logged in to Bluesky as {handle}")
            return True
        except Exception as e:
            logger.error(f"Failed to log in to Bluesky: {e}")
            self.authenticated = False
            return False
    
    def get_post_details(self, post_uri: str) -> Optional[Dict[str, Any]]:
        """
        Get details about a post.
        
        Args:
            post_uri: URI of the post to get details for
            
        Returns:
            Dict containing post details or None if not found
        """
        if not self._check_client():
            return None
            
        try:
            post_data = self.client.app.bsky.feed.get_post_thread({
                "uri": post_uri
            })
            
            post = post_data.thread.post
            author = post.author.display_name or post.author.handle
            
            logger.info(f"Retrieved post by {author}: \"{post.record.text[:100]}...\"")
            
            return {
                "uri": post.uri,
                "author": {
                    "did": post.author.did,
                    "handle": post.author.handle,
                    "display_name": post.author.display_name
                },
                "text": post.record.text,
                "created_at": post.record.created_at
            }
        except Exception as e:
            logger.error(f"Failed to get post details: {e}")
            return None
    
    def get_post_replies(self, post_uri: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Get replies to a post.
        
        Args:
            post_uri: URI of the post to get replies for
            depth: Depth of replies to retrieve (default: 1 for direct replies only)
            
        Returns:
            List of reply data dictionaries
        """
        if not self._check_client():
            return []
            
        try:
            thread_data = self.client.app.bsky.feed.get_post_thread({
                "uri": post_uri,
                "depth": depth
            })
            
            replies = []
            
            # Extract replies from the thread
            if hasattr(thread_data.thread, "replies") and thread_data.thread.replies:
                for reply in thread_data.thread.replies:
                    reply_data = {
                        "uri": reply.post.uri,
                        "author": {
                            "did": reply.post.author.did,
                            "handle": reply.post.author.handle,
                            "display_name": reply.post.author.display_name
                        },
                        "text": reply.post.record.text,
                        "created_at": reply.post.record.created_at
                    }
                    replies.append(reply_data)
            
            return replies
        except Exception as e:
            logger.error(f"Error getting post replies: {e}")
            return []
    
    def _check_client(self) -> bool:
        """Check if the client is authenticated."""
        if not self.client or not self.authenticated:
            logger.error("Bluesky client not authenticated")
            return False
        return True


def web_url_to_at_uri(url: str) -> Optional[str]:
    """
    Convert a Bluesky web URL to an AT Protocol URI.
    
    Args:
        url: Bluesky web URL (e.g., https://bsky.app/profile/handle.bsky.social/post/recordid)
        
    Returns:
        AT URI or None if conversion failed
    """
    # Extract handle and record ID from URL
    pattern = r"https?://bsky\.app/profile/([^/]+)/post/([^/]+)"
    match = re.match(pattern, url)
    
    if not match:
        logger.error(f"Invalid Bluesky URL format: {url}")
        return None
    
    handle = match.group(1)
    record_id = match.group(2)
    
    # Resolve handle to DID
    try:
        response = requests.get(
            "https://bsky.social/xrpc/com.atproto.identity.resolveHandle", 
            params={"handle": handle}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to resolve handle {handle}: {response.text}")
            return None
        
        did = response.json().get("did")
        
        # Construct AT URI
        at_uri = f"at://{did}/app.bsky.feed.post/{record_id}"
        logger.info(f"Converted URL to AT URI: {at_uri}")
        
        return at_uri
    except Exception as e:
        logger.error(f"Error converting URL to AT URI: {e}")
        return None 