#!/usr/bin/env python3
"""
Bluesky API Example - Using atproto SDK
"""

from atproto import Client
import os
import json


def login(handle, password):
    """Login to Bluesky"""
    client = Client()
    client.login(handle, password)
    print(f"Successfully logged in as {handle}")
    return client


def get_timeline(client, limit=20):
    """Get posts from your timeline"""
    feed = client.app.bsky.feed.get_timeline({"limit": limit})
    posts = []
    
    print(f"\n--- Your Timeline (Latest {limit} Posts) ---")
    for i, post in enumerate(feed.feed, 1):
        author = post.post.author.display_name or post.post.author.handle
        text = post.post.record.text
        
        print(f"{i}. {author}: {text[:100]}{'...' if len(text) > 100 else ''}")
        posts.append({
            "author": author,
            "handle": post.post.author.handle,
            "text": text,
            "created_at": post.post.record.created_at,
        })
    
    return posts


def create_post(client, text, reply_to=None):
    """Create a new post"""
    response = client.send_post(text, reply_to=reply_to)
    print(f"\nPost created successfully: {response.uri}")
    return response


def get_user_posts(client, handle, limit=10):
    """Get posts from a specific user"""
    feed = client.app.bsky.feed.get_author_feed({"actor": handle, "limit": limit})
    
    print(f"\n--- Latest {limit} Posts from {handle} ---")
    for i, post in enumerate(feed.feed, 1):
        text = post.post.record.text
        print(f"{i}. {text[:100]}{'...' if len(text) > 100 else ''}")
    
    return feed.feed


def search_posts(client, query, limit=10):
    """Search for posts containing a query"""
    results = client.app.bsky.feed.search_posts({"q": query, "limit": limit})
    
    print(f"\n--- Search Results for '{query}' ---")
    for i, post in enumerate(results.posts, 1):
        author = post.author.display_name or post.author.handle
        text = post.record.text
        print(f"{i}. {author}: {text[:100]}{'...' if len(text) > 100 else ''}")
    
    return results.posts


def follow_user(client, handle):
    """Follow a user by handle"""
    did = client.resolve_handle(handle).did
    follow = client.app.bsky.graph.follow.create({"subject": did})
    print(f"\nFollowed {handle} successfully!")
    return follow


def get_followers(client, handle, limit=50):
    """Get a list of a user's followers"""
    did = client.resolve_handle(handle).did
    followers = client.app.bsky.graph.get_followers({"actor": did, "limit": limit})
    
    print(f"\n--- {handle}'s Followers ---")
    for i, follower in enumerate(followers.followers, 1):
        name = follower.display_name or follower.handle
        print(f"{i}. {name} (@{follower.handle})")
    
    return followers.followers


def main():
    """Main function to demonstrate Bluesky API usage"""
    # Use environment variables for credentials (more secure)
    # You can set these with:
    # export BLUESKY_HANDLE="yourhandle.bsky.social"
    # export BLUESKY_APP_PASSWORD="your-app-password"
    
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    
    if not handle or not password:
        print("Please set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables")
        handle = input("Or enter your handle (e.g., 'yourname.bsky.social'): ")
        password = input("Enter your app password (generate one at https://bsky.app/settings/app-passwords): ")
    
    # Login
    try:
        client = login(handle, password)
    except Exception as e:
        print(f"Login failed: {e}")
        return
    
    # Example operations
    try:
        # Get timeline
        timeline_posts = get_timeline(client, limit=5)
        
        # Get posts from a specific user
        get_user_posts(client, "bsky.app", limit=3)
        
        # Search for posts
        search_posts(client, "Python", limit=3)
        
        # Uncomment to post (be careful when testing)
        # create_post(client, "Testing the Bluesky API with Python!")
        
        # Uncomment to follow a user (be careful when testing)
        # follow_user(client, "bsky.app")
        
        # Get followers
        # get_followers(client, handle, limit=5)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 