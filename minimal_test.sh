#!/bin/bash
# Minimal Redpanda Auth Test

# Set Redpanda Cloud configuration
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS=cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092
export REDPANDA_CLOUD_USERNAME=backend
export REDPANDA_CLOUD_PASSWORD=jQZzu9x3z0WKsjWLmE9ZLf44fKoXag

# Execute the test script
echo "Testing Redpanda authentication..."

python ./minimal_test.py \
  --sasl_mechanism "PLAIN" \
  --debug

echo "Test complete!" 