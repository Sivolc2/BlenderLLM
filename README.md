# Bluesky API Examples

This repository contains examples of interacting with the Bluesky API (via the AT Protocol) using Python.

## Requirements

For the SDK-based example:
```bash
pip install atproto
```

For the raw HTTP example:
```bash
pip install requests
```

## Setup

You need a Bluesky account with an app password to use these examples.

1. Create an app password at https://bsky.app/settings/app-passwords
2. Set environment variables (recommended for security):

```bash
export BLUESKY_HANDLE="yourhandle.bsky.social"
export BLUESKY_APP_PASSWORD="your-app-password"
```

Alternatively, you can enter your credentials when prompted by the script.

## Usage

### Using the SDK

Run the example script that uses the atproto SDK:

```bash
python bluesky_api_example.py
```

### Using Raw HTTP Requests

If you want to understand how the API works at a lower level without the SDK:

```bash
python bluesky_api_raw.py
```

## Features

The scripts demonstrate:

- Authentication with Bluesky
- Fetching your timeline
- Getting posts from a specific user
- Searching for posts by keyword
- Creating new posts (commented out by default)
- Following users (commented out by default)
- Getting a user's followers

## Security Note

- Never commit your app password to version control
- Use environment variables or a secure secrets manager
- The app password has the same access as your account, so treat it with care

## Resources

- [AT Protocol Documentation](https://atproto.com)
- [Bluesky Documentation](https://docs.bsky.app)
- [Bluesky Website](https://bsky.app)

# MasterpieceX 3D Generator

This repository also includes examples of generating 3D models using the MasterpieceX API.

## Requirements

Install the required packages:

```bash
pip install mpx-genai-sdk requests
```

For the full integration with Blender rendering, you'll also need Blender installed on your system.

## Setup

You need a MasterpieceX account with API credits to use this example.

1. Create an account at [MasterpieceX](https://www.masterpiecex.com/) 
2. Get your API key from the dashboard
3. Set the environment variable:

```bash
export MPX_API_KEY="your-masterpiece-api-key"
```

## Usage

### Basic Generation

Generate a 3D model from a text prompt:

```bash
python masterpiecex.py --prompt "A steampunk robot with gears and pipes"
```

### Direct Download of Existing Models

Download an existing model from a MasterpieceX URL:

```bash
python masterpiecex_direct.py --url "https://app.masterpiecex.com/generate/history/QpozDiykmQpVEsH8iZ2Y"
```

This allows you to download a model you've previously generated without using additional credits.

#### Options for Direct Download

```
--url              URL of existing MasterpieceX model (required)
--name             Custom name for the output folder (default: derived from model ID) 
--output_folder    Where to save files (default: output/)
--format           Format to download: obj, glb, or all (default: obj)
--debug            Enable debug logging
--api_key          MasterpieceX API key (defaults to MPX_API_KEY environment variable)
--force            Force redownload even if files already exist
```

### Full Integration with Blender

Generate a model and automatically render it with Blender:

```bash
python masterpiecex_integration.py --prompt "A steampunk robot with gears and pipes"
```

This script combines:
1. MasterpieceX's 3D generation capabilities
2. Automatic Blender rendering of the 3D model

### Options

```
--prompt            Text description of what to create (required)
--output_folder     Where to save files (default: output/)
--poll_interval     Seconds between generation status checks (default: 10)
--max_wait          Maximum time to wait for generation in seconds (default: 600)
--blender_executable Path to Blender (auto-detected on macOS)
--brightness        Lighting brightness (Very Bright, Bright, Medium Bright, Dark, Very Dark)
--debug             Enable debug logging
--simulate          Simulate API calls for testing (no actual API calls made)
```

### Testing Without API Credits

You can use simulation mode to test the workflow without making actual API calls:

```bash
# Test just the generation part
python masterpiecex.py --prompt "A simple cube" --simulate

# Test the full generation and rendering pipeline
python masterpiecex_integration.py --prompt "A simple cube" --simulate
```

This creates a basic cube OBJ file to simulate the API response, allowing you to test the entire workflow without using API credits.

## Three.js Animation Export

You can also export your 3D models to interactive Three.js web pages with animations:

```bash
python threejs_animation.py --obj_path path/to/your/model.obj --animation_type bounce
```

### Animation Options:

- `--obj_path`: Path to your OBJ file (required)
- `--output_dir`: Custom output directory (defaults to same as OBJ)
- `--title`: Custom title for the web page (defaults to filename)
- `--animation_type`: Animation type (`rotate`, `bounce`, or `spin`)
- `--camera_distance`: Adjust camera distance from model (default: 5.0)
- `--scene_color`: Set background color (hex, default: 0x1a1a1a)
- `--debug`: Enable detailed logging

## Redpanda Cloud Integration

Export your 3D models to Redpanda Cloud for streaming and real-time applications.

### Requirements

Install the required packages:

```bash
pip install kafka-python
```

### Setup

Configure your Redpanda Cloud connection details:

```bash
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS="your-bootstrap-servers"
export REDPANDA_CLOUD_GEOJSON_TOPIC="your-topic"
export REDPANDA_CLOUD_USERNAME="your-username"
export REDPANDA_CLOUD_PASSWORD="your-password"
```

### Exporting Models to Redpanda

Use the export script to send a GLB model to Redpanda Cloud:

```bash
python export_to_redpanda.py --glb_path "/path/to/your/model.glb"
```

### Options for Exporting

```
--glb_path           Path to the GLB file to export (required)
--topic              Redpanda topic to publish to
--bootstrap_servers  Redpanda Cloud bootstrap servers
--username           Redpanda Cloud username
--password           Redpanda Cloud password
--model_id           Model ID (defaults to filename without extension)
--model_name         Model name (defaults to model_id)
--max_message_bytes  Maximum message size in bytes (default: 5MB)
--split_size         Split large models into chunks of this size in bytes
--sasl_mechanism     SASL mechanism (SCRAM-SHA-256, SCRAM-SHA-512)
--debug              Enable debug logging
--timeout            Timeout in seconds for operations (default: 30)
```

### Handling Large Models

The exporter provides two strategies for handling large 3D models:

#### 1. Increased Message Size Limits

For models up to 5MB, you can increase the Kafka message size limits:

```bash
python export_to_redpanda.py --glb_path "/path/to/your/model.glb" --max_message_bytes 5242880
```

This approach keeps the entire model in a single message but requires Redpanda server configuration that supports large messages.

#### 2. Chunking Large Models (Recommended)

For very large models or when server limits cannot be changed, use chunking:

```bash
python export_to_redpanda.py --glb_path "/path/to/your/model.glb" --split_size 100000
```

This will split the model into 100KB chunks and send them as separate messages with metadata to allow reconstruction. The consumer will need to reassemble the chunks.

Based on our testing, chunking with a relatively small chunk size (100KB) works more reliably than trying to send larger messages.

### Authentication Mechanisms

Redpanda Cloud supports different authentication mechanisms, with SCRAM-SHA-256 being the most commonly used:

```bash
python export_to_redpanda.py --glb_path "/path/to/your/model.glb" --sasl_mechanism "SCRAM-SHA-256"
```

The supported authentication mechanisms include:
- SCRAM-SHA-256 (default and recommended)
- SCRAM-SHA-512

### Timeout and Error Handling

The export script includes built-in timeout handling to prevent hanging:

```bash
python export_to_redpanda.py --glb_path "/path/to/your/model.glb" --timeout 60
```

This will set a 60-second timeout for operations, helping to prevent the script from hanging indefinitely. If an operation exceeds the timeout, the script will exit with an error message.

You can also interrupt the script at any time with Ctrl+C for a clean exit.

### Quick Export

For convenience, use the provided shell script to export a specific model:

```bash
./export_model.sh
```

This script sets up all necessary environment variables and exports the model to Redpanda Cloud using chunking and SCRAM-SHA-256 authentication.
