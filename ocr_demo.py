#!/usr/bin/env python3
"""Example script demonstrating OCR functionality with DeepSeek OCR."""

import os
import sys
import argparse
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from epollo.ocr_utils import DeepSeekOCR
from epollo.screenshot import render_url_to_screenshot_sync
from epollo.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_ocr_from_file(image_path: str, output_format: str = "plain", auto_crop: bool = False):
    logger.info(f"Extracting text from {image_path} using format: {output_format}, auto_crop: {auto_crop}")
    
    try:
        config = Config()
        ocr = DeepSeekOCR(
            api_url=config.ocr_api_url,
            model=config.ocr_model,
            timeout=config.ocr_timeout
        )
        
        if not ocr.check_connection():
            logger.error("Cannot connect to Ollama API. Make sure Ollama is running with DeepSeek OCR model.")
            return False
        
        if output_format.lower() == "tables":
            result = ocr.extract_tables(image_path, auto_crop=auto_crop)
        else:
            result = ocr.extract_structured_text(image_path, output_format, auto_crop=auto_crop)
        
        print(f"\n{'='*60}")
        print(f"EXTRACTED TEXT ({output_format.upper()} FORMAT)")
        print(f"{'='*60}")
        print(result)
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return False


def demo_ocr_from_url(url: str, output_format: str = "plain", save_screenshot: bool = True, auto_crop: bool = False):
    logger.info(f"Taking screenshot of {url}")
    
    try:
        screenshot_path = f"screenshot_{url.replace('https://', '').replace('http://', '').replace('/', '_')}.png" if save_screenshot else None
        screenshot_bytes = render_url_to_screenshot_sync(
            url=url,
            output_path=screenshot_path,
            width=1200,
            height=800,
            format='png'
        )
        
        return demo_ocr_from_bytes(screenshot_bytes, output_format, auto_crop)
        
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        return False


def demo_ocr_from_bytes(image_bytes: bytes, output_format: str = "plain", auto_crop: bool = False):
    logger.info(f"Extracting text from image bytes using format: {output_format}, auto_crop: {auto_crop}")
    
    try:
        config = Config()
        ocr = DeepSeekOCR(
            api_url=config.ocr_api_url,
            model=config.ocr_model,
            timeout=config.ocr_timeout
        )
        
        if not ocr.check_connection():
            logger.error("Cannot connect to Ollama API. Make sure Ollama is running with DeepSeek OCR model.")
            return False
        
        if output_format.lower() == "tables":
            result = ocr.extract_tables(image_bytes, auto_crop=auto_crop)
        else:
            result = ocr.extract_structured_text(image_bytes, output_format, auto_crop=auto_crop)
        
        print(f"\n{'='*60}")
        print(f"EXTRACTED TEXT ({output_format.upper()} FORMAT)")
        print(f"{'='*60}")
        print(result)
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DeepSeek OCR Demo")
    parser.add_argument("input", help="Image file path or URL to process")
    parser.add_argument("--format", choices=["plain", "markdown", "html", "tables"], 
                       default="plain", help="Output format (default: plain)")
    parser.add_argument("--type", choices=["file", "url"], default="file",
                       help="Input type (file or url, default: file)")
    parser.add_argument("--no-save", action="store_true", help="Don't save screenshots when processing URLs")
    parser.add_argument("--auto-crop", action="store_true", help="Automatically crop tall images (height > 2x width)")
    
    args = parser.parse_args()
    
    logger.info("Starting DeepSeek OCR demo")
    
    if args.type == "file":
        if not os.path.exists(args.input):
            logger.error(f"File not found: {args.input}")
            sys.exit(1)
        
        success = demo_ocr_from_file(args.input, args.format, args.auto_crop)
    
    elif args.type == "url":
        success = demo_ocr_from_url(args.input, args.format, not args.no_save, args.auto_crop)
    
    else:
        logger.error(f"Unknown input type: {args.type}")
        sys.exit(1)
    
    if success:
        logger.info("OCR demo completed successfully")
        sys.exit(0)
    else:
        logger.error("OCR demo failed")
        sys.exit(1)


if __name__ == "__main__":
    main()