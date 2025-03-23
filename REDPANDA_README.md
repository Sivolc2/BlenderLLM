# Simple Redpanda Client

A basic producer-consumer example for Redpanda/Kafka using the `kafka-python` package. This client demonstrates how to produce and consume messages to/from Redpanda, supporting both local development clusters and Redpanda Cloud.

## Features

- Upload text files to a Redpanda topic
- Consume messages from a Redpanda topic
- Support for SASL authentication (for Redpanda Cloud)
- Command-line interface for easy testing

## Prerequisites

- Python 3.x
- A running Redpanda cluster (local or cloud)
- Python virtual environment (recommended)

## Quick Start

1. Set up a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. For local Redpanda usage:

Run a local Redpanda cluster using Docker:

```bash
docker run -d --name=redpanda-1 --rm \
  -p 9092:9092 \
  -p 9644:9644 \
  redpandadata/redpanda:latest \
  redpanda start \
  --kafka-addr PLAINTEXT://0.0.0.0:9092 \
  --advertise-kafka-addr PLAINTEXT://127.0.0.1:9092
```

Create a test topic:

```bash
docker exec -it redpanda-1 rpk topic create test-topic
```

3. For Redpanda Cloud:

Set the following environment variables:

```bash
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS=<your-bootstrap-servers>
export REDPANDA_CLOUD_USERNAME=<your-username>
export REDPANDA_CLOUD_PASSWORD=<your-password>
```

## Usage

The client can be used directly from the command line or via the provided shell script.

### Using the Shell Script

Upload a test message:

```bash
./redpanda_demo.sh produce
```

Consume messages:

```bash
./redpanda_demo.sh consume
```

Upload and then consume:

```bash
./redpanda_demo.sh both
```

### Using Direct Command Line

Upload a file:

```bash
python redpanda_simple_client.py --mode produce \
  --file test_message.txt \
  --topic test-topic \
  --bootstrap_servers localhost:9092
```

Consume messages:

```bash
python redpanda_simple_client.py --mode consume \
  --topic test-topic \
  --bootstrap_servers localhost:9092
```

### Using with Redpanda Cloud

```bash
python redpanda_simple_client.py --mode produce \
  --file test_message.txt \
  --topic your-topic \
  --bootstrap_servers your-bootstrap-servers \
  --username your-username \
  --password your-password
```

## Extending the Client

This is a simple example that can be extended in several ways:

1. Add schema registry support for Avro/Protobuf serialization
2. Implement batch processing for larger files
3. Add compression options for messages
4. Add more sophisticated error handling and retries

## Troubleshooting

- If you encounter connection issues, check that your Redpanda cluster is running
- For authentication errors with Redpanda Cloud, verify your credentials
- For local clusters, ensure the ports are correctly exposed (9092 for Kafka protocol) 