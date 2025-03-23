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

# Check if Redpanda is enabled
if grep -q "REDPANDA_CLOUD_BOOTSTRAP_SERVERS" .env; then
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
    $REDPANDA_FLAG 