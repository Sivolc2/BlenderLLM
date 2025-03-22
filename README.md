# Bluesky API Examples

This repository contains examples of interacting with the Bluesky API (via the AT Protocol) using Python.

## Requirements

For the SDK-based example:
```bash
pip install atproto
```

For the raw HTTP example:
```bash
pip install requests
```

## Setup

You need a Bluesky account with an app password to use these examples.

1. Create an app password at https://bsky.app/settings/app-passwords
2. Set environment variables (recommended for security):

```bash
export BLUESKY_HANDLE="yourhandle.bsky.social"
export BLUESKY_APP_PASSWORD="your-app-password"
```

Alternatively, you can enter your credentials when prompted by the script.

## Usage

### Using the SDK

Run the example script that uses the atproto SDK:

```bash
python bluesky_api_example.py
```

### Using Raw HTTP Requests

If you want to understand how the API works at a lower level without the SDK:

```bash
python bluesky_api_raw.py
```

## Features

The scripts demonstrate:

- Authentication with Bluesky
- Fetching your timeline
- Getting posts from a specific user
- Searching for posts by keyword
- Creating new posts (commented out by default)
- Following users (commented out by default)
- Getting a user's followers

## Security Note

- Never commit your app password to version control
- Use environment variables or a secure secrets manager
- The app password has the same access as your account, so treat it with care

## Resources

- [AT Protocol Documentation](https://atproto.com)
- [Bluesky Documentation](https://docs.bsky.app)
- [Bluesky Website](https://bsky.app)
