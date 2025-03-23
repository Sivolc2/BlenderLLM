# Unified Bluesky Monitor with Redpanda Integration

A complete solution for monitoring Bluesky post replies and integrating with Redpanda for event streaming.

## Overview

This project provides a modular, unified solution that:

1. Monitors a specific Bluesky post for new replies in real-time
2. Sends notifications to Redpanda when new replies are detected
3. Operates with a customizable polling frequency (default: 5 seconds)
4. Supports both web URLs and AT Protocol URIs for posts

The solution is designed following SOLID principles, with clean separation of concerns and modular architecture.

## Solution Components

The solution consists of the following components:

- **Bluesky Client**: Handles interactions with the Bluesky API
- **Redpanda Client**: Manages connections and message passing with Redpanda
- **Reply Monitor**: Core monitoring logic that coordinates the components
- **Command-line Interface**: Unified interface for configuration and operation

## Installation

The project uses a modular architecture organized in a Python package:

```
bsky_monitor/            # Main package
├── modules/             # Core functionality modules
│   ├── bluesky_client.py  # Bluesky API interactions
│   ├── redpanda_client.py # Redpanda interactions
│   └── monitor.py       # Reply monitoring logic
├── __init__.py          # Package initialization
└── __main__.py          # Command-line entry point
```

### Quick Start

The easiest way to use the solution is with the included launcher script:

```bash
# Run the demo with a specific post URL
./demo-bsky-monitor.sh "https://bsky.app/profile/geocubed.bsky.social/post/3lkz43wfzzm2t"

# Or run directly with more options
./bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123"
```

### Environment Setup

Create a `.env` file with your credentials:

```
BLUESKY_HANDLE=yourhandle.bsky.social
BLUESKY_APP_PASSWORD=your-app-password

# Optional Redpanda credentials
REDPANDA_CLOUD_BOOTSTRAP_SERVERS=your-redpanda-server:9092
REDPANDA_CLOUD_USERNAME=your-redpanda-username
REDPANDA_CLOUD_PASSWORD=your-redpanda-password
```

## Usage

### Command Line Options

```
usage: bsky-monitor [-h] (--post-url POST_URL | --post-uri POST_URI)
                   [--handle HANDLE] [--password PASSWORD]
                   [--poll-interval POLL_INTERVAL]
                   [--redpanda-servers REDPANDA_SERVERS]
                   [--redpanda-topic REDPANDA_TOPIC]
                   [--redpanda-username REDPANDA_USERNAME]
                   [--redpanda-password REDPANDA_PASSWORD] [--no-redpanda]
                   [--debug]
```

### Common Usage Patterns

```bash
# Monitor with faster polling (2 seconds)
./bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123" --poll-interval 2

# Monitor without Redpanda integration
./bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123" --no-redpanda

# Using the AT Protocol URI directly
./bsky-monitor --post-uri "at://did:plc:abcdef/app.bsky.feed.post/123"

# Custom Redpanda configuration
./bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123" \
  --redpanda-servers "custom-server:9092" \
  --redpanda-topic "custom-topic-name"
```

## Design Principles

The solution follows these design principles:

1. **Modularity**: Components are organized into separate modules with clear responsibilities
2. **SOLID Principles**:
   - **Single Responsibility**: Each class has a single responsibility
   - **Open-Closed**: Extendable without modifying existing code
   - **Liskov Substitution**: Components use clean interfaces
   - **Interface Segregation**: Clean separation between different concerns
   - **Dependency Inversion**: High-level modules don't depend on low-level details
3. **Configuration Flexibility**: Multiple ways to configure (env vars, command line)
4. **Error Handling**: Robust error handling throughout the codebase

## Redpanda Integration

When a new reply is detected, a message is sent to Redpanda with the following format:

```json
{
  "event_type": "new_reply",
  "timestamp": "2023-08-15T12:34:56.789Z",
  "post_uri": "at://did:plc:abcdef/app.bsky.feed.post/123456",
  "reply": {
    "uri": "at://did:plc:uvwxyz/app.bsky.feed.post/789012",
    "author": {
      "did": "did:plc:uvwxyz",
      "handle": "replier.bsky.social",
      "display_name": "Replier"
    },
    "text": "This is a reply to the post",
    "created_at": "2023-08-15T12:34:50.000Z"
  }
}
```

These messages can be consumed by other services for further processing, analytics, or integrations.

## Advanced Features

### Custom Polling Rate

Adjust the polling rate to balance between real-time updates and API load:

```bash
# Poll every 10 seconds
POLL_INTERVAL=10 ./demo-bsky-monitor.sh "https://bsky.app/profile/handle.bsky.social/post/123"
```

### Debugging

Enable debug mode for more detailed logging:

```bash
./bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123" --debug
```

## Sample Application Ideas

This solution can be used for:

1. **Real-time Analytics**: Analyze reply patterns and content
2. **Moderation Tools**: Flag potentially problematic replies for review
3. **Community Engagement**: Respond quickly to important discussions
4. **Archiving**: Preserve discussions for historical records
5. **Custom Notifications**: Send alerts based on reply content or authors

## License

See the LICENSE file for details. 