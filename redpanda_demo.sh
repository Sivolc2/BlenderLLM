#!/bin/bash
# Demo script for Redpanda client

# # Set up the Python virtual environment if needed
# if [ ! -d "venv" ]; then
#     echo "Creating virtual environment..."
#     python3 -m venv venv
#     source venv/bin/activate
#     pip install --upgrade pip
#     pip install -r requirements.txt
# else
#     source venv/bin/activate
# fi

# If using Redpanda Cloud, uncomment and set these variables
# export REDPANDA_CLOUD_BOOTSTRAP_SERVERS=cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092
# export REDPANDA_CLOUD_USERNAME=backend
# export REDPANDA_CLOUD_PASSWORD=jQZzu9x3z0WKsjWLmE9ZLf44fKoXag

# Set topic name
TOPIC="test-topic"

# Function to produce a message
produce_message() {
    echo "Uploading test message to Redpanda..."
    python redpanda_simple_client.py --mode produce \
        --file test_message.txt \
        --topic $TOPIC \
        --bootstrap_servers ${REDPANDA_CLOUD_BOOTSTRAP_SERVERS:-"localhost:9092"}
        
    if [ $? -eq 0 ]; then
        echo "✅ Message uploaded successfully!"
    else
        echo "❌ Failed to upload message"
        exit 1
    fi
}

# Function to consume messages
consume_messages() {
    echo "Consuming messages from Redpanda..."
    echo "Press Ctrl+C to stop"
    
    python redpanda_simple_client.py --mode consume \
        --topic $TOPIC \
        --bootstrap_servers ${REDPANDA_CLOUD_BOOTSTRAP_SERVERS:-"localhost:9092"}
}

# Main execution
case "$1" in
    produce)
        produce_message
        ;;
    consume)
        consume_messages
        ;;
    both)
        produce_message
        echo "--------------------------"
        echo "Now consuming messages..."
        consume_messages
        ;;
    *)
        echo "Usage: $0 {produce|consume|both}"
        echo "  produce - Upload test message to Redpanda"
        echo "  consume - Read messages from Redpanda"
        echo "  both    - Upload and then consume messages"
        exit 1
        ;;
esac

exit 0 