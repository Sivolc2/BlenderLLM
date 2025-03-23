# Bluesky Reply Monitor with Redpanda

A utility that monitors replies to a specific Bluesky post and sends notifications to Redpanda when new replies are detected.

## Features

- Monitors a specific Bluesky post for new replies
- Sends notifications to Redpanda for each new reply detected
- Configurable polling interval
- Support for authentication with both Bluesky and Redpanda

## Requirements

- Python 3.7+
- A Bluesky account with an app password
- Redpanda instance (local or cloud)

## Installation

1. Clone this repository or download the source files
2. Make the monitor script executable:
   ```bash
   chmod +x monitor_bluesky_replies.sh
   ```
3. Set up a Python virtual environment (the script will do this automatically if needed)

## Configuration

### Environment Variables

You can configure the monitor using environment variables:

- `BLUESKY_HANDLE`: Your Bluesky handle/username
- `BLUESKY_APP_PASSWORD`: Your Bluesky app password
- `REDPANDA_CLOUD_BOOTSTRAP_SERVERS`: Redpanda bootstrap servers
- `REDPANDA_CLOUD_USERNAME`: Redpanda username (if using SASL)
- `REDPANDA_CLOUD_PASSWORD`: Redpanda password (if using SASL)
- `POLL_INTERVAL`: Time in seconds between checks (default: 60)
- `REDPANDA_TOPIC`: Redpanda topic name (default: "bluesky-replies")

These can be set in a `.env` file in the project directory.

## Usage

### Basic Usage

```bash
./monitor_bluesky_replies.sh --post-uri "at://did:plc:abcdef/app.bsky.feed.post/123456"
```

### Advanced Options

```bash
./monitor_bluesky_replies.sh \
  --post-uri "at://did:plc:abcdef/app.bsky.feed.post/123456" \
  --handle "yourhandle.bsky.social" \
  --password "your-app-password" \
  --poll-interval 30 \
  --redpanda-servers "localhost:9092" \
  --redpanda-topic "custom-topic-name" \
  --debug
```

### Command Line Options

- `--post-uri <URI>`: URI of the Bluesky post to monitor (required)
- `--handle <handle>`: Bluesky handle/username
- `--password <password>`: Bluesky app password
- `--poll-interval <seconds>`: Time between checks in seconds (default: 60)
- `--redpanda-servers <list>`: Redpanda bootstrap servers
- `--redpanda-topic <topic>`: Redpanda topic name
- `--redpanda-username <username>`: Redpanda SASL username
- `--redpanda-password <password>`: Redpanda SASL password
- `--debug`: Enable debug logging
- `--help`: Show help message

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

## How It Works

1. The script authenticates with Bluesky using the provided credentials
2. It retrieves the initial post and records any existing replies
3. At regular intervals, it checks for new replies to the post
4. When a new reply is detected, it sends a notification to Redpanda
5. The notification includes details about the reply and the original post

## License

See the LICENSE file for details.

## Troubleshooting

- If you encounter SSL certificate errors with Redpanda, make sure your environment has the appropriate CA certificates installed
- For authentication issues with Bluesky, verify your handle and app password are correct
- If no messages are being sent to Redpanda, check your connection details and ensure the topic exists 