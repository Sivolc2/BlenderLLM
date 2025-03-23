#!/bin/bash
# Bluesky Monitor Demo Script

# Check for required argument
if [ -z "$1" ]; then
    echo "Usage: $0 <bluesky-post-url>"
    echo "Example: $0 https://bsky.app/profile/geocubed.bsky.social/post/3lkz43wfzzm2t"
    exit 1
fi

POST_URL="$1"

# Print banner
echo "============================================"
echo "🔍 Bluesky Reply Monitor with Redpanda Demo"
echo "============================================"
echo ""
echo "📝 Post URL: $POST_URL"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "You need to create a .env file with your Bluesky credentials:"
    echo ""
    echo "BLUESKY_HANDLE=yourhandle.bsky.social"
    echo "BLUESKY_APP_PASSWORD=your-app-password"
    echo ""
    echo "Optionally, you can add Redpanda credentials:"
    echo "REDPANDA_CLOUD_BOOTSTRAP_SERVERS=your-redpanda-server:9092"
    echo "REDPANDA_CLOUD_USERNAME=your-redpanda-username"
    echo "REDPANDA_CLOUD_PASSWORD=your-redpanda-password"
    exit 1
fi

# Default options
POLL_INTERVAL=${POLL_INTERVAL:-5}
REDPANDA_FLAG="--no-redpanda"
REDPANDA_CREDENTIALS=""
REDPANDA_TOPIC=""

# Check if Redpanda is enabled
if grep -q "REDPANDA_CLOUD_BOOTSTRAP_SERVERS" .env; then
    # Check if we have credentials in env vars, otherwise look in .env
    if [ -n "$REDPANDA_CLOUD_USERNAME" ] && [ -n "$REDPANDA_CLOUD_PASSWORD" ]; then
        echo "🔑 Using Redpanda credentials from environment"
    elif grep -q "REDPANDA_CLOUD_USERNAME" .env && grep -q "REDPANDA_CLOUD_PASSWORD" .env; then
        echo "🔑 Using Redpanda credentials from .env file"
    else
        # Default credentials for demo purposes
        echo "🔑 Using default Redpanda credentials"
        export REDPANDA_CLOUD_USERNAME=backend
        export REDPANDA_CLOUD_PASSWORD=jQZzu9x3z0WKsjWLmE9ZLf44fKoXag
    fi
    
    # Set the topic from environment or env file
    if [ -n "$REDPANDA_CLOUD_GEOJSON_TOPIC" ]; then
        REDPANDA_TOPIC="--redpanda-topic $REDPANDA_CLOUD_GEOJSON_TOPIC"
        echo "📨 Using Redpanda topic: $REDPANDA_CLOUD_GEOJSON_TOPIC"
    elif grep -q "REDPANDA_CLOUD_GEOJSON_TOPIC" .env; then
        TOPIC=$(grep "REDPANDA_CLOUD_GEOJSON_TOPIC" .env | cut -d"=" -f2)
        REDPANDA_TOPIC="--redpanda-topic $TOPIC"
        echo "📨 Using Redpanda topic from .env: $TOPIC"
    else
        echo "⚠️ No Redpanda topic specified, using default"
    fi
    
    REDPANDA_FLAG=""
    echo "🚀 Redpanda integration enabled"
else
    echo "ℹ️ Redpanda integration disabled"
fi

echo "⏱️ Poll interval: ${POLL_INTERVAL} seconds"
echo ""
echo "Starting monitor..."
echo "(Press Ctrl+C to stop)"
echo ""

# Run the monitor
./bsky-monitor \
    --post-url "$POST_URL" \
    --poll-interval "$POLL_INTERVAL" \
    $REDPANDA_TOPIC \
    $REDPANDA_FLAG 