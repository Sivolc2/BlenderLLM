#!/bin/bash
# Redpanda Test Helper
# A simple script to test various types of uploads to Redpanda

# Set Redpanda connection details (from export_model_url.sh)
export REDPANDA_CLOUD_BOOTSTRAP_SERVERS="cvfklfhfq53j10ap5ku0.any.us-east-1.mpx.prd.cloud.redpanda.com:9092"
export REDPANDA_CLOUD_GEOJSON_TOPIC="geojson-data"
export REDPANDA_CLOUD_USERNAME="backend"
export REDPANDA_CLOUD_PASSWORD="jQZzu9x3z0WKsjWLmE9ZLf44fKoXag"

# Function to print section header
print_header() {
    echo "=============================================="
    echo "  $1"
    echo "=============================================="
}

# Function to test text file upload
test_text_upload() {
    print_header "TESTING TEXT FILE UPLOAD"
    python simple_redpanda_upload.py
}

# Function to test JSON file upload
test_json_upload() {
    print_header "TESTING JSON FILE UPLOAD"
    python simple_json_upload.py
}

# Function to create a custom test file
create_custom_test_file() {
    local content="$1"
    local filename="$2"
    
    echo -e "$content" > "$filename"
    echo "Created test file: $filename"
}

# Main menu
show_menu() {
    clear
    print_header "REDPANDA TEST HELPER"
    echo "1. Test text file upload (simple_test.txt)"
    echo "2. Test JSON file upload (test_json_message.json)"
    echo "3. Create and upload a custom text file"
    echo "4. Create and upload a custom JSON file"
    echo "5. Exit"
    echo
    echo -n "Enter your choice [1-5]: "
}

# Function to create and upload a custom text file
create_and_upload_text() {
    print_header "CREATE AND UPLOAD CUSTOM TEXT FILE"
    
    echo -n "Enter filename (e.g., custom_test.txt): "
    read filename
    
    echo "Enter file content (end with Ctrl+D on a new line):"
    content=$(cat)
    
    create_custom_test_file "$content" "$filename"
    
    # Modify simple_redpanda_upload.py to use the custom file
    sed -i '' "s/INPUT_FILE = \".*\"/INPUT_FILE = \"$filename\"/" simple_redpanda_upload.py
    
    # Run the upload
    python simple_redpanda_upload.py
    
    # Reset the file back to the original
    sed -i '' "s/INPUT_FILE = \".*\"/INPUT_FILE = \"simple_test.txt\"/" simple_redpanda_upload.py
}

# Function to create and upload a custom JSON file
create_and_upload_json() {
    print_header "CREATE AND UPLOAD CUSTOM JSON FILE"
    
    echo -n "Enter filename (e.g., custom_data.json): "
    read filename
    
    echo "Enter JSON content (valid JSON format, end with Ctrl+D on a new line):"
    content=$(cat)
    
    # Validate JSON
    if echo "$content" | jq . > /dev/null 2>&1; then
        create_custom_test_file "$content" "$filename"
        
        # Modify simple_json_upload.py to use the custom file
        sed -i '' "s/INPUT_FILE = \".*\"/INPUT_FILE = \"$filename\"/" simple_json_upload.py
        
        # Run the upload
        python simple_json_upload.py
        
        # Reset the file back to the original
        sed -i '' "s/INPUT_FILE = \".*\"/INPUT_FILE = \"test_json_message.json\"/" simple_json_upload.py
    else
        echo "Error: Invalid JSON format. Please try again."
    fi
}

# Main loop
while true; do
    show_menu
    read choice
    
    case $choice in
        1) test_text_upload ;;
        2) test_json_upload ;;
        3) create_and_upload_text ;;
        4) create_and_upload_json ;;
        5) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid option. Press Enter to continue..."; read ;;
    esac
    
    echo
    echo "Press Enter to continue..."
    read
done