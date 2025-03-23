#!/bin/bash
# Monitor Bluesky Replies - Wrapper script

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Virtual environment check and setup
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
    else
        echo "Installing required packages..."
        pip install atproto kafka-python
    fi
fi

# Check for required environment variables
if [ -z "$BLUESKY_HANDLE" ] || [ -z "$BLUESKY_APP_PASSWORD" ]; then
    if [ -f ".env" ]; then
        echo "Loading environment variables from .env file..."
        export $(grep -v '^#' .env | xargs)
    else
        echo "Warning: BLUESKY_HANDLE and BLUESKY_APP_PASSWORD are required"
        echo "You will be prompted to enter them when the script runs"
    fi
fi

# Default values
POLL_INTERVAL=${POLL_INTERVAL:-60}
REDPANDA_TOPIC=${REDPANDA_TOPIC:-"bluesky-replies"}

# Help function
show_help() {
    echo "Usage: $0 [options] --post-uri <URI>"
    echo ""
    echo "Monitor replies to a Bluesky post and send notifications to Redpanda"
    echo ""
    echo "Options:"
    echo "  --post-uri <URI>           URI of the Bluesky post to monitor (required)"
    echo "  --handle <handle>          Bluesky handle/username (default: \$BLUESKY_HANDLE)"
    echo "  --password <password>      Bluesky app password (default: \$BLUESKY_APP_PASSWORD)"
    echo "  --poll-interval <seconds>  Time between checks in seconds (default: 60)"
    echo "  --redpanda-servers <list>  Redpanda bootstrap servers (default: localhost:9092)"
    echo "  --redpanda-topic <topic>   Redpanda topic name (default: bluesky-replies)"
    echo "  --debug                    Enable debug logging"
    echo "  --help                     Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  BLUESKY_HANDLE             Your Bluesky handle"
    echo "  BLUESKY_APP_PASSWORD       Your Bluesky app password"
    echo "  REDPANDA_CLOUD_BOOTSTRAP_SERVERS Redpanda servers"
    echo "  REDPANDA_CLOUD_USERNAME    Redpanda username (if using SASL)"
    echo "  REDPANDA_CLOUD_PASSWORD    Redpanda password (if using SASL)"
    echo ""
    echo "Example:"
    echo "  $0 --post-uri at://did:plc:abcdef/app.bsky.feed.post/123456"
    exit 1
}

# Parse arguments
ARGS=""
POST_URI=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help)
            show_help
            ;;
        --post-uri)
            POST_URI="$2"
            ARGS="$ARGS --post-uri $2"
            shift 2
            ;;
        --handle|--password|--poll-interval|--redpanda-servers|--redpanda-topic|--redpanda-username|--redpanda-password|--debug)
            ARGS="$ARGS $1"
            if [[ "$1" != "--debug" ]]; then
                ARGS="$ARGS $2"
                shift
            fi
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Check for required post URI
if [ -z "$POST_URI" ]; then
    echo "Error: --post-uri is required"
    show_help
fi

# Run the monitor
echo "Starting Bluesky reply monitor..."
echo "Post URI: $POST_URI"
echo "Redpanda topic: $REDPANDA_TOPIC"

python bluesky_reply_monitor.py $ARGS

# Deactivate the virtual environment
deactivate 