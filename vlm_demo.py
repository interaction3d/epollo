#!/usr/bin/env python3
"""Example script demonstrating VLM functionality with Qwen3-VL for news headline extraction."""

import os
import sys
import argparse
from pathlib import Path
import logging
import base64

# Add the epollo package to the path
sys.path.insert(0, str(Path(__file__).parent))

from epollo.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROMPT = "Please read the image and extract news headlines"
MODEL = "qwen3-vl:2b"


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def query_vlm(image_path: str, prompt: str = PROMPT, model: str = MODEL) -> str:
    """Query the VLM model with an image and prompt.
    
    Args:
        image_path: Path to the image file
        prompt: The prompt to send to the model
        model: The VLM model to use
        
    Returns:
        The model's response text
    """
    config = Config()
    api_url = config.ollama_api_url
    
    import requests
    
    # Encode image to base64
    image_base64 = encode_image_to_base64(image_path)
    
    # Prepare the request - using /api/generate endpoint like OCR
    url = f"{api_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 2048
        }
    }
    
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    
    result = response.json()
    return result.get("response", "")


def demo_vlm_from_file(image_path: str, prompt: str = PROMPT, model: str = MODEL):
    """Demonstrate VLM on an existing image file.
    
    Args:
        image_path: Path to image file
        prompt: Prompt to send to the VLM
        model: VLM model name
    """
    logger.info(f"Processing {image_path} with model: {model}")
    
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"File not found: {image_path}")
            return False
        
        # Query the VLM
        result = query_vlm(image_path, prompt, model)
        
        print(f"\n{'='*60}")
        print(f"VLM RESPONSE ({model})")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}")
        print(result)
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return False


def main():
    """Main function to run VLM demo."""
    parser = argparse.ArgumentParser(description="Qwen3-VL News Headline Extraction Demo")
    parser.add_argument("input", help="Image file path to process")
    parser.add_argument("--prompt", default=PROMPT, help="Prompt to send to the VLM")
    parser.add_argument("--model", default=MODEL, help="VLM model to use (default: qwen3-vl:2b)")
    
    args = parser.parse_args()
    
    logger.info("Starting Qwen3-VL demo")
    
    success = demo_vlm_from_file(args.input, args.prompt, args.model)
    
    if success:
        logger.info("VLM demo completed successfully")
        sys.exit(0)
    else:
        logger.error("VLM demo failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
