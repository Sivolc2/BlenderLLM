# Bluesky Monitor

A modular Python package that monitors Bluesky posts for replies and sends notifications to Redpanda.

## Features

- Monitor any Bluesky post for new replies
- Adjustable polling interval (default: 5 seconds)
- Automatic conversion from web URLs to AT Protocol URIs
- Integration with Redpanda for event streaming
- Clean, modular architecture following SOLID principles
- Installable as a Python package

## Installation

### Quick Start

The easiest way to use the monitor is with the included launcher script:

```bash
./bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123"
```

The launcher script takes care of setting up the virtual environment and installing dependencies.

### Manual Installation

If you prefer to install the package manually:

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package
pip install -e .
```

## Usage

### Command Line

```bash
# Using web URL (automatically converted to AT URI)
bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123"

# Using AT Protocol URI directly
bsky-monitor --post-uri "at://did:plc:abcdef/app.bsky.feed.post/123"

# Customize polling interval
bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123" --poll-interval 10

# Disable Redpanda integration
bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123" --no-redpanda

# Connect to a specific Redpanda instance
bsky-monitor --post-url "https://bsky.app/profile/handle.bsky.social/post/123" \
  --redpanda-servers "redpanda:9092" \
  --redpanda-topic "custom-topic-name"
```

### Environment Variables

You can use environment variables to configure authentication:

```bash
export BLUESKY_HANDLE="yourhandle.bsky.social"
export BLUESKY_APP_PASSWORD="your-app-password"
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS="redpanda-server:9092"
export REDPANDA_CLOUD_USERNAME="redpanda-username"
export REDPANDA_CLOUD_PASSWORD="redpanda-password"
```

Alternatively, you can place these in a `.env` file in the project directory.

### Full Options

```
usage: bsky-monitor [-h] (--post-url POST_URL | --post-uri POST_URI)
                  [--handle HANDLE] [--password PASSWORD]
                  [--poll-interval POLL_INTERVAL]
                  [--redpanda-servers REDPANDA_SERVERS]
                  [--redpanda-topic REDPANDA_TOPIC]
                  [--redpanda-username REDPANDA_USERNAME]
                  [--redpanda-password REDPANDA_PASSWORD] [--no-redpanda]
                  [--debug]

Bluesky Post Monitor with Redpanda Integration

options:
  -h, --help            show this help message and exit
  --post-url POST_URL   Bluesky post URL (e.g.,
                        https://bsky.app/profile/handle.bsky.social/post/xyz)
  --post-uri POST_URI   AT Protocol URI of the post to monitor
  --handle HANDLE       Bluesky handle/username
  --password PASSWORD   Bluesky app password
  --poll-interval POLL_INTERVAL
                        Time in seconds between checks for new replies
                        (default: 5)
  --redpanda-servers REDPANDA_SERVERS
                        Redpanda bootstrap servers
  --redpanda-topic REDPANDA_TOPIC
                        Redpanda topic for notifications
  --redpanda-username REDPANDA_USERNAME
                        Redpanda SASL username
  --redpanda-password REDPANDA_PASSWORD
                        Redpanda SASL password
  --no-redpanda         Skip Redpanda integration (monitoring only)
  --debug               Enable debug logging
```

## Architecture

The package follows a modular architecture with clean separation of concerns:

- **BlueskyClient**: Handles interactions with the Bluesky API
- **RedpandaClient**: Manages connections and message passing with Redpanda
- **ReplyMonitor**: Core monitoring logic that coordinates the components

This design aligns with SOLID principles:

- **Single Responsibility**: Each module handles a specific concern
- **Open-Closed**: Extendable with new features without modifying existing code
- **Liskov Substitution**: Components use well-defined interfaces
- **Interface Segregation**: Clean interfaces between modules
- **Dependency Inversion**: High-level modules don't depend on low-level implementations

## Redpanda Message Format

Messages sent to Redpanda have the following format:

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

## Development

### Project Structure

```
bsky_monitor/
├── __init__.py         # Package initialization
├── __main__.py         # Command-line entry point
├── modules/            # Core functionality modules
│   ├── __init__.py     # Module exports
│   ├── bluesky_client.py  # Bluesky API interactions
│   ├── redpanda_client.py # Redpanda interactions
│   └── monitor.py      # Reply monitoring logic
└── README.md           # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See the LICENSE file for details. 