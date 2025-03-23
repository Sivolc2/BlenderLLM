#!/bin/bash
# Export MasterpieceX model URL to Redpanda Cloud (lightweight version)

# Set Redpanda Cloud configuration
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS=cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092
export REDPANDA_CLOUD_GEOJSON_TOPIC=geojson-data
export REDPANDA_CLOUD_USERNAME=backend
export REDPANDA_CLOUD_PASSWORD=jQZzu9x3z0WKsjWLmE9ZLf44fKoXag

# Model ID and name
MODEL_ID="QpozDiykmQpVEsH8iZ2Y"
MODEL_NAME="MasterpieceX 3D Model"

# Execute the export script
echo "Exporting model URL to Redpanda Cloud..."

python ./export_model_url.py \
  --model_id "$MODEL_ID" \
  --model_name "$MODEL_NAME" \
  --bootstrap_servers "$REDPANDA_CLOUD_BOOTSTRAP_SERVERS" \
  --username "$REDPANDA_CLOUD_USERNAME" \
  --password "$REDPANDA_CLOUD_PASSWORD" \
  --topic "$REDPANDA_CLOUD_GEOJSON_TOPIC" \
  --sasl_mechanism "SCRAM-SHA-256" \
  --timeout 30 \
  --debug

echo "Export complete!" 