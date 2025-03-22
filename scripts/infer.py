from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
import requests
import json
import re
import logging
import anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlenderLLM")

def extract_blender_script(response):
    """Extract script from response, adding tags if they're not present."""
    # Check if the response already has the tags
    if "<blender-script>" in response and "</blender-script>" in response:
        # Extract script within the tags
        pattern = r"<blender-script>(.*?)</blender-script>"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # If there are code blocks (```python or just ```), extract from those
    python_pattern = r"```(?:python)?\s*(import bpy.*?)```"
    match = re.search(python_pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no tags or code blocks but has import bpy, assume the whole thing is a script
    if "import bpy" in response:
        # Try to find where the script actually starts
        lines = response.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if "import bpy" in line:
                start_idx = i
                break
        
        return '\n'.join(lines[start_idx:]).strip()
    
    # If we can't identify a script, log a warning and return the original
    logger.warning("Could not identify a clear Blender script in the model output")
    return response

def validate_script(script):
    """Validate that the script is a valid Blender script."""
    if not script.strip():
        logger.error("Empty script generated")
        return False
    
    if "import bpy" not in script:
        logger.error("Generated script doesn't import bpy module")
        return False
    
    return True

def generate_response(model_name: str, prompt: str, max_new_tokens: int = 512) -> str:
    """Generate a Blender script response from the model."""
    logger.info(f"Generating script using model: {model_name}")
    
    # Add specific instructions to wrap output in tags
    system_prompt = (
        "You are an expert in using bpy script to create 3D models. Based on the following instruction, "
        "your task is to write the corresponding bpy script that will generate the desired 3D model in Blender. "
        "Please pay close attention to every detail in the script and ensure it fully adheres to the provided specifications.\n\n"
        "YOUR RESPONSE MUST FOLLOW THIS FORMAT EXACTLY:\n"
        "<blender-script>\n"
        "import bpy\n"
        "# Your Blender Python code here\n"
        "</blender-script>\n\n"
        "1. Do not include any explanations before or after the script tags\n"
        "2. Do not use markdown formatting or code blocks\n"
        "3. The script must start with 'import bpy'\n"
        "4. Include code to clear any existing objects in the scene\n"
        "5. Ensure your script creates the 3D model as described in the prompt"
    )
    
    # Check if it's a remote API call
    if model_name.startswith("openai:"):
        raw_response = generate_from_api(model_name, prompt, system_prompt, max_new_tokens)
    elif model_name.startswith("anthropic:"):
        raw_response = generate_from_anthropic(model_name, prompt, system_prompt, max_new_tokens)
    elif model_name.startswith("api:"):
        raw_response = generate_from_api(model_name, prompt, system_prompt, max_new_tokens)
    else:
        # Local model inference
        raw_response = generate_from_local_model(model_name, prompt, system_prompt, max_new_tokens)
    
    # Extract the script from the response
    script = extract_blender_script(raw_response)
    
    # Validate the script
    if not validate_script(script):
        logger.warning("Validation failed, but returning script anyway")
    
    # Log script length for debugging
    logger.info(f"Generated script with {len(script.split())} words and {len(script.splitlines())} lines")
    
    return script

def generate_from_local_model(model_name, prompt, system_prompt, max_new_tokens):
    """Generate a response using a local model."""
    logger.info("Loading local model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    logger.info("Local model loaded successfully")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    logger.info("Generating response...")
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=max_new_tokens
    )

    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    logger.info("Response generated successfully")
    
    return response

def generate_from_api(model_name: str, prompt: str, system_prompt: str, max_new_tokens: int = 512) -> str:
    """Generate response using remote API services like OpenAI"""
    logger.info(f"Using remote API: {model_name}")
    
    # Handle OpenAI API
    if model_name.startswith("openai:"):
        model = model_name.split(":", 1)[1]  # Get model name after "openai:"
        api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_new_tokens
        }
        
        logger.info(f"Sending request to OpenAI API for model: {model}")
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                logger.info("OpenAI API request successful")
                return result
            else:
                logger.error(f"API Error: {response.text}")
                raise Exception(f"API Error: {response.text}")
        except Exception as e:
            logger.error(f"Error in API request: {str(e)}")
            raise
    
    # Handle custom API endpoints
    elif model_name.startswith("api:"):
        endpoint = model_name.split(":", 1)[1]  # Get endpoint after "api:"
        api_key = os.environ.get("CUSTOM_API_KEY")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_new_tokens
        }
        
        logger.info(f"Sending request to custom API: {endpoint}")
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                logger.info("Custom API request successful")
                return result
            else:
                logger.error(f"API Error: {response.text}")
                raise Exception(f"API Error: {response.text}")
        except Exception as e:
            logger.error(f"Error in API request: {str(e)}")
            raise
    
    else:
        raise ValueError("Unsupported API format. Use 'openai:model-name' or 'api:endpoint-url'")

def generate_from_anthropic(model_name: str, prompt: str, system_prompt: str, max_new_tokens: int = 512) -> str:
    """Generate response using Anthropic Claude API"""
    logger.info(f"Using Anthropic API: {model_name}")
    
    # Supported Claude models
    supported_models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20240620",
        "claude-3-7-sonnet-20240708"  # Latest Claude 3.7 Sonnet
    ]
    
    # Extract model name after "anthropic:"
    model = model_name.split(":", 1)[1]
    
    # Verify the model is supported
    if model not in supported_models and not model.startswith("claude-"):
        logger.warning(f"Model '{model}' is not in the list of known Claude models: {supported_models}")
        logger.warning("The request may fail if the model name is incorrect")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    
    try:
        # Create anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        
        logger.info(f"Sending request to Anthropic API for model: {model}")
        
        # Adjust max tokens based on model capabilities
        # Claude 3.7 Sonnet has increased capabilities
        if "3-7" in model:
            max_tokens = min(8192, max_new_tokens * 4)  # Higher limit for Claude 3.7
        else:
            max_tokens = min(4096, max_new_tokens * 4)  # Standard limit for other models
        
        # Create message with system prompt and user prompt
        response = client.messages.create(
            model=model,
            system=system_prompt,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.content[0].text
        logger.info("Anthropic API request successful")
        return result
        
    except Exception as e:
        logger.error(f"Error in Anthropic API request: {str(e)}")
        raise

if __name__ == "__main__":
    model_name = "BlenderLLM"
    prompt = "Please drow a cube."
    result = generate_response(model_name, prompt)
    print("Generated Response:\n", result)
