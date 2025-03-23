# Bluesky Monitor

A modular Python package that monitors Bluesky posts for replies and sends notifications to Redpanda.

## Features

- Monitor any Bluesky post for new replies
- Adjustable polling interval (default: 5 seconds)
- Automatic conversion from web URLs to AT Protocol URIs
- Integration with Redpanda for event streaming
- Clean, modular architecture following SOLID principles
- Robust reconnection handling for Redpanda
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
# Bluesky credentials
export BLUESKY_HANDLE="yourhandle.bsky.social"
export BLUESKY_APP_PASSWORD="your-app-password"

# Redpanda configuration
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS="your-redpanda-server:9092"
export REDPANDA_CLOUD_USERNAME="your-redpanda-username"
export REDPANDA_CLOUD_PASSWORD="your-redpanda-password"
export REDPANDA_CLOUD_GEOJSON_TOPIC="your-topic-name"
```

Alternatively, you can place these in a `.env` file in the project directory.

### Redpanda Setup

To use the Redpanda integration, you need to provide the following credentials:

1. **Bootstrap Servers**: The Redpanda broker address (hostname:port)
2. **Authentication**: Username and password for SASL/SCRAM authentication
3. **Topic**: The topic to which notifications will be sent

You can set these up using environment variables directly:

```bash
export REDPANDA_CLOUD_USERNAME=your-username
export REDPANDA_CLOUD_PASSWORD=your-password
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS=your-server:9092
export REDPANDA_CLOUD_GEOJSON_TOPIC=your-topic
```

Or by adding them to your `.env` file.

### Consuming Messages from Redpanda

A consumer script is included to verify messages being sent to the Redpanda topic:

```bash
# Set environment variables if not in .env
export REDPANDA_CLOUD_USERNAME=your-username
export REDPANDA_CLOUD_PASSWORD=your-password
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS=your-server:9092
export REDPANDA_CLOUD_GEOJSON_TOPIC=your-topic

# Run the consumer script
python redpanda_consumer.py
```

You can also specify arguments directly:

```bash
python redpanda_consumer.py --bootstrap-servers "your-server:9092" --topic "your-topic" --username "your-username" --password "your-password"
```

The consumer script will display any new messages received on the specified topic, making it easy to verify that the integration is working correctly.

### Verifying Redpanda Connection

To verify that your Redpanda connection is working correctly, you can use the included test script:

```bash
# Set environment variables if not in .env
export REDPANDA_CLOUD_USERNAME=your-username
export REDPANDA_CLOUD_PASSWORD=your-password

# Run the test script
python test_redpanda.py
```

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
- **RedpandaClient**: Manages connections and message passing with Redpanda, with built-in reconnection logic
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

## Troubleshooting

### Redpanda Connection Issues

If you're having trouble connecting to Redpanda, you can:

1. Verify your credentials with the test script: `python test_redpanda.py`
2. Check message delivery with the consumer script: `python redpanda_consumer.py`
3. Ensure your Redpanda server is accessible from your network
4. Check that the SASL/SCRAM authentication is correctly set up
5. Run with the `--debug` flag to see more detailed connection logs

### Handling Disconnections

The system now includes automatic reconnection logic for Redpanda with the following features:

- Automatic reconnection attempts when a connection is lost
- Exponential backoff strategy to avoid overwhelming the server
- Graceful handling of temporary network issues
- Continued monitoring even if Redpanda is unavailable

If you see "Connection error when sending to Redpanda" messages, the system will automatically try to reconnect up to 3 times before giving up on that particular message. Monitoring will continue regardless, and new messages will trigger fresh connection attempts.

### Missing or Invalid Credentials

If you see "Redpanda not connected" or "Failed to connect to Redpanda" errors:

1. Make sure your environment variables are correctly set
2. Verify that your credentials are valid 
3. Ensure the bootstrap servers address is correct and accessible

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