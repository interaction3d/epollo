#!/usr/bin/env python3
"""Example script demonstrating VLM functionality with Qwen3-VL for news headline extraction."""

import os
import sys
import argparse
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from epollo.vlm_utils import Qwen3VL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROMPT = "Please read the image and extract news headlines"
MODEL = "qwen3-vl:2b"


def demo_vlm_from_file(image_path: str, prompt: str = PROMPT, model: str = MODEL):
    logger.info(f"Processing {image_path} with model: {model}")
    
    try:
        if not os.path.exists(image_path):
            logger.error(f"File not found: {image_path}")
            return False
        
        vlm = Qwen3VL(model=model)
        result = vlm.query(image_path, prompt)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"VLM RESPONSE ({model})")
        logger.info(f"Prompt: {prompt}")
        logger.info(f"{'='*60}")
        logger.info(result)
        logger.info(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return False


def main():
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
