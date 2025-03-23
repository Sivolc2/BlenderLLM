#!/usr/bin/env python3
"""
Convert Bluesky Web URL to AT Protocol URI
"""

import sys
import argparse
import requests
import re

def extract_components_from_url(url):
    """Extract handle and record ID from Bluesky URL."""
    pattern = r"https?://bsky\.app/profile/([^/]+)/post/([^/]+)"
    match = re.match(pattern, url)
    
    if not match:
        raise ValueError(f"Invalid Bluesky URL format: {url}")
    
    handle = match.group(1)
    record_id = match.group(2)
    
    return handle, record_id

def resolve_handle_to_did(handle):
    """Resolve a Bluesky handle to a DID."""
    response = requests.get(f"https://bsky.social/xrpc/com.atproto.identity.resolveHandle", 
                          params={"handle": handle})
    
    if response.status_code != 200:
        raise Exception(f"Failed to resolve handle: {response.text}")
    
    return response.json().get("did")

def construct_at_uri(did, record_id):
    """Construct an AT URI from a DID and record ID."""
    return f"at://{did}/app.bsky.feed.post/{record_id}"

def main():
    parser = argparse.ArgumentParser(description="Convert Bluesky Web URL to AT Protocol URI")
    parser.add_argument("url", help="Bluesky web URL (e.g., https://bsky.app/profile/handle.bsky.social/post/recordid)")
    args = parser.parse_args()
    
    try:
        handle, record_id = extract_components_from_url(args.url)
        did = resolve_handle_to_did(handle)
        at_uri = construct_at_uri(did, record_id)
        
        print(f"Handle: {handle}")
        print(f"DID: {did}")
        print(f"Record ID: {record_id}")
        print(f"AT URI: {at_uri}")
        
        print("\nTo monitor this post, run:")
        print(f"./monitor_bluesky_replies.sh --post-uri \"{at_uri}\"")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 