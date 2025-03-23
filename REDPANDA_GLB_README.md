# Redpanda GLB Uploader

A set of tools to upload GLB 3D model files to Redpanda Cloud.

## Overview

This package contains scripts for uploading GLB (glTF Binary) 3D model files to Redpanda Cloud. Two upload methods are provided:

1. **Single-message upload**: Uploads the entire GLB file as a single message (suitable for small files)
2. **Chunked upload**: Splits the GLB file into smaller chunks and sends them as separate messages (recommended for larger files)

## Files

- `upload_glb_file.py` - Uploads a GLB file as a single message
- `upload_glb_chunked.py` - Uploads a GLB file in chunks
- `upload_glb.sh` - Shell script to simplify running the uploaders

## Prerequisites

- Python 3.x
- `kafka-python` library
- Redpanda Cloud credentials

## Usage

### Using the Shell Script (Recommended)

The simplest way to upload a GLB file is using the provided shell script:

```bash
# Upload the default GLB file (from the output folder)
./upload_glb.sh

# Upload a specific GLB file
./upload_glb.sh path/to/model.glb

# Upload using chunked method (recommended for large files)
./upload_glb.sh --chunked

# Upload with custom chunk size (e.g., 200KB chunks)
./upload_glb.sh --chunked --chunk-size 200 path/to/model.glb
```

### Using Python Scripts Directly

For more control, you can use the Python scripts directly:

```bash
# Upload entire file at once
python upload_glb_file.py path/to/model.glb

# Upload file in chunks
python upload_glb_chunked.py path/to/model.glb [chunk_size_in_kb]
```

## How It Works

### Single-Message Upload

The single-message uploader:
1. Reads the entire GLB file
2. Encodes it as base64
3. Creates a JSON message with metadata and the encoded file
4. Sends it to the specified Redpanda topic

### Chunked Upload

The chunked uploader:
1. Calculates the file size and splits it into chunks
2. Sends a metadata message with file information (size, hash, etc.)
3. Sends each chunk as a separate message with sequence information
4. Sends a completion message when all chunks are sent

This approach is more reliable for large files and avoids message size limitations.

## Configuration

The scripts use the following environment variables:

- `REDPANDA_CLOUD_BOOTSTRAP_SERVERS` - Redpanda bootstrap servers
- `REDPANDA_CLOUD_GEOJSON_TOPIC` - Redpanda topic name
- `REDPANDA_CLOUD_USERNAME` - SASL username
- `REDPANDA_CLOUD_PASSWORD` - SASL password

These are set in the shell script and can be overridden.

## Example Message Format

### Metadata Message
```json
{
  "model_id": "mpx_model_QpozDiykmQpVEsH8iZ2Y",
  "timestamp": "2025-03-22T18:16:17Z",
  "transfer_id": "mpx_model_QpozDiykmQpVEsH8iZ2Y-2025-03-22T18:16:17Z-5b9f469e",
  "filename": "mpx_model_QpozDiykmQpVEsH8iZ2Y.glb",
  "content_type": "model/gltf-binary",
  "file_size": 1575040,
  "chunk_size": 102400,
  "num_chunks": 16,
  "hash": "5b9f469e511f1a9c46253af059e3d4159b8007e295d854cc2071e99e3d0da4ef",
  "type": "metadata"
}
```

### Chunk Message
```json
{
  "transfer_id": "mpx_model_QpozDiykmQpVEsH8iZ2Y-2025-03-22T18:16:17Z-5b9f469e",
  "chunk_index": 0,
  "total_chunks": 16,
  "chunk_size": 102400,
  "data": "base64_encoded_chunk_data...",
  "type": "chunk"
}
```

### Completion Message
```json
{
  "transfer_id": "mpx_model_QpozDiykmQpVEsH8iZ2Y-2025-03-22T18:16:17Z-5b9f469e",
  "timestamp": "2025-03-22T18:16:41Z",
  "status": "complete",
  "num_chunks_sent": 16,
  "file_size": 1575040,
  "hash": "5b9f469e511f1a9c46253af059e3d4159b8007e295d854cc2071e99e3d0da4ef",
  "type": "completion"
}
```

## Troubleshooting

- **Timeouts**: If you experience timeouts, try reducing the chunk size and increasing the delay between chunks
- **Memory issues**: For very large files, the chunked uploader is recommended to avoid memory limitations
- **Authentication errors**: Verify your Redpanda Cloud credentials

## Consumer Implementation

To consume the uploaded GLB file:

1. For single-message uploads: Read the message and decode the base64 content
2. For chunked uploads:
   - Find the metadata message for the desired transfer_id
   - Collect all chunk messages with the same transfer_id
   - Sort chunks by chunk_index
   - Concatenate the decoded data from all chunks
   - Verify the final file hash matches the one in the metadata message 