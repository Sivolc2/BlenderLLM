#!/bin/bash
# GLB Uploader Script
# A simple shell script to upload GLB files to Redpanda

# Set Redpanda connection details (from export_model_url.sh)
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS="cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092"
export REDPANDA_CLOUD_GEOJSON_TOPIC="geojson-data"
export REDPANDA_CLOUD_USERNAME="backend"
export REDPANDA_CLOUD_PASSWORD="jQZzu9x3z0WKsjWLmE9ZLf44fKoXag"

# Default GLB file
DEFAULT_GLB_FILE="output/mpx_model_QpozDiykmQpVEsH8iZ2Y/mpx_model_QpozDiykmQpVEsH8iZ2Y.glb"

# Print header
print_header() {
    echo "=============================================="
    echo "  $1"
    echo "=============================================="
}

# Check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        echo "❌ Error: File '$1' not found"
        exit 1
    fi
    
    local file_size=$(ls -la "$1" | awk '{print $5}')
    echo "✅ Found file: $1 ($(numfmt --to=iec-i --suffix=B $file_size))"
}

# Show help
show_help() {
    echo "Usage: $0 [OPTIONS] [GLB_FILE]"
    echo
    echo "Uploads a GLB file to Redpanda."
    echo
    echo "Options:"
    echo "  -c, --chunked       Upload the file in chunks (recommended for large files)"
    echo "  -s, --chunk-size    Chunk size in KB (default: 500)"
    echo "  -h, --help          Show this help message"
    echo
    echo "Examples:"
    echo "  $0                         Upload the default GLB file"
    echo "  $0 path/to/model.glb       Upload a specific GLB file"
    echo "  $0 -c path/to/model.glb    Upload a specific GLB file in chunks"
    echo "  $0 -c -s 200 model.glb     Upload with 200KB chunks"
}

# Main execution
main() {
    # Parse arguments
    local use_chunked=false
    local chunk_size=100
    local glb_file="$DEFAULT_GLB_FILE"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--chunked)
                use_chunked=true
                shift
                ;;
            -s|--chunk-size)
                chunk_size="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                # Assume it's the GLB file
                glb_file="$1"
                shift
                ;;
        esac
    done
    
    # Check if the file exists
    check_file "$glb_file"
    
    # Upload the file
    if $use_chunked; then
        print_header "UPLOADING GLB FILE IN CHUNKS"
        echo "File: $glb_file"
        echo "Chunk size: ${chunk_size}KB"
        
        # Execute the chunked upload
        python upload_glb_chunked.py "$glb_file" "$chunk_size"
    else
        print_header "UPLOADING GLB FILE"
        echo "File: $glb_file"
        
        # Execute the regular upload
        python upload_glb_file.py "$glb_file"
    fi
}

# Execute main function with all arguments
main "$@" 