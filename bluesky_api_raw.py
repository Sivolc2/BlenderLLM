#!/usr/bin/env python3
"""
Bluesky API Raw HTTP Example - No SDK
"""

import requests
import json
import os

# API Base URL
ATP_HOST = "https://bsky.social/xrpc"

def create_session():
    """Create a session with persistent cookies and default headers"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    return session

def login(session, handle, password):
    """Login to Bluesky with handle and app password"""
    login_data = {
        "identifier": handle,
        "password": password
    }
    
    response = session.post(
        f"{ATP_HOST}/com.atproto.server.createSession",
        json=login_data
    )
    
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    
    auth_data = response.json()
    print(f"Successfully logged in as {handle}")
    
    # Save the JWT token for future requests
    session.headers.update({
        "Authorization": f"Bearer {auth_data.get('accessJwt')}"
    })
    
    return auth_data

def get_timeline(session, limit=20):
    """Get posts from your timeline"""
    response = session.get(
        f"{ATP_HOST}/app.bsky.feed.getTimeline",
        params={"limit": limit}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get timeline: {response.text}")
    
    data = response.json()
    feed = data.get('feed', [])
    
    print(f"\n--- Your Timeline (Latest {limit} Posts) ---")
    for i, post in enumerate(feed, 1):
        author = post.get('post', {}).get('author', {})
        record = post.get('post', {}).get('record', {})
        
        author_name = author.get('displayName') or author.get('handle', 'Unknown')
        text = record.get('text', '')
        
        print(f"{i}. {author_name}: {text[:100]}{'...' if len(text) > 100 else ''}")
    
    return feed

def create_post(session, text):
    """Create a new post (or "skeet")"""
    # First get your DID
    response = session.get(f"{ATP_HOST}/com.atproto.server.getSession")
    if response.status_code != 200:
        raise Exception("Failed to get session")
    
    session_data = response.json()
    did = session_data.get('did')
    
    # Create the post
    post_data = {
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.datetime.now().isoformat()
        }
    }
    
    response = session.post(
        f"{ATP_HOST}/com.atproto.repo.createRecord",
        json=post_data
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to create post: {response.text}")
    
    data = response.json()
    uri = data.get('uri', '')
    print(f"\nPost created successfully: {uri}")
    
    return data

def get_user_profile(session, handle):
    """Get a user's profile by handle"""
    response = session.get(
        f"{ATP_HOST}/app.bsky.actor.getProfile",
        params={"actor": handle}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get profile: {response.text}")
    
    profile = response.json()
    print(f"\n--- Profile for {handle} ---")
    print(f"Display Name: {profile.get('displayName', 'None')}")
    print(f"Description: {profile.get('description', 'None')}")
    print(f"Followers: {profile.get('followersCount', 0)}")
    print(f"Following: {profile.get('followsCount', 0)}")
    print(f"Posts: {profile.get('postsCount', 0)}")
    
    return profile

def get_user_posts(session, handle, limit=10):
    """Get posts from a specific user"""
    response = session.get(
        f"{ATP_HOST}/app.bsky.feed.getAuthorFeed",
        params={"actor": handle, "limit": limit}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get user posts: {response.text}")
    
    data = response.json()
    feed = data.get('feed', [])
    
    print(f"\n--- Latest {limit} Posts from {handle} ---")
    for i, post in enumerate(feed, 1):
        record = post.get('post', {}).get('record', {})
        text = record.get('text', '')
        print(f"{i}. {text[:100]}{'...' if len(text) > 100 else ''}")
    
    return feed

def search_posts(session, query, limit=10):
    """Search for posts containing a query"""
    response = session.get(
        f"{ATP_HOST}/app.bsky.feed.searchPosts",
        params={"q": query, "limit": limit}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to search posts: {response.text}")
    
    data = response.json()
    posts = data.get('posts', [])
    
    print(f"\n--- Search Results for '{query}' ---")
    for i, post in enumerate(posts, 1):
        author = post.get('author', {})
        author_name = author.get('displayName') or author.get('handle', 'Unknown')
        text = post.get('record', {}).get('text', '')
        print(f"{i}. {author_name}: {text[:100]}{'...' if len(text) > 100 else ''}")
    
    return posts

def main():
    """Main function to demonstrate Bluesky API usage with raw HTTP requests"""
    # Use environment variables for credentials (more secure)
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    
    if not handle or not password:
        print("Please set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables")
        handle = input("Or enter your handle (e.g., 'yourname.bsky.social'): ")
        password = input("Enter your app password (generate one at https://bsky.app/settings/app-passwords): ")
    
    # Create session
    session = create_session()
    
    try:
        # Login
        auth_data = login(session, handle, password)
        
        # Example API calls
        get_timeline(session, limit=5)
        get_user_profile(session, "bsky.app")
        get_user_posts(session, "bsky.app", limit=3)
        search_posts(session, "Python", limit=3)
        
        # Uncomment to create a post (be careful when testing)
        # import datetime
        # create_post(session, "Testing the Bluesky API with raw HTTP requests!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 