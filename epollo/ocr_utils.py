"""OCR utility functions using DeepSeek OCR via Ollama API."""

import os
import base64
import logging
from typing import Optional, Dict, Any, Union, List, Tuple
from pathlib import Path
import requests
from PIL import Image
import io
import tempfile

logger = logging.getLogger(__name__)


class DeepSeekOCR:
    """DeepSeek OCR client using Ollama API."""
    
    def __init__(
        self,
        api_url: str = "http://localhost:11434",
        model: str = "deepseek-ocr",
        timeout: int = 60
    ):
        """Initialize DeepSeek OCR client.
        
        Args:
            api_url: Ollama API base URL
            model: Model name for DeepSeek OCR
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.ocr_url = f"{self.api_url}/api/generate"
        self.max_aspect_ratio = 2.0
    
    def _encode_image(self, image_path: Union[str, Path, bytes, Image.Image]) -> str:
        """Encode image to base64 string.
        
        Args:
            image_path: Path to image file, image bytes, or PIL Image
            
        Returns:
            Base64 encoded image string
        """
        if isinstance(image_path, (str, Path)):
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
        elif isinstance(image_path, bytes):
            image_bytes = image_path
        elif isinstance(image_path, Image.Image):
            buffer = io.BytesIO()
            image_path.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
        else:
            raise ValueError("image_path must be file path, bytes, or PIL Image")
        
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _crop_tall_image(self, image: Union[str, Path, bytes, Image.Image]) -> List[Image.Image]:
        """Crop tall image into multiple sections if aspect ratio exceeds max_aspect_ratio.
        
        Args:
            image: Image to crop
            
        Returns:
            List of cropped PIL Image objects
        """
        # Load image
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        elif isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        elif isinstance(image, Image.Image):
            img = image.copy()
        else:
            raise ValueError("image must be file path, bytes, or PIL Image")
        
        width, height = img.size
        aspect_ratio = height / width
        
        logger.info(f"Image dimensions: {width}x{height}, aspect ratio: {aspect_ratio:.2f}")
        
        # If aspect ratio is acceptable, return as single image
        if aspect_ratio <= self.max_aspect_ratio:
            logger.info("Aspect ratio is within limits, no cropping needed")
            return [img]
        
        # Calculate crop dimensions
        crop_height = int(width * self.max_aspect_ratio)
        num_crops = (height + crop_height - 1) // crop_height  # Ceiling division
        
        logger.info(f"Image too tall (aspect ratio {aspect_ratio:.2f}). Splitting into {num_crops} crops")
        
        cropped_images = []
        for i in range(num_crops):
            # Calculate crop boundaries
            start_y = i * crop_height
            end_y = min((i + 1) * crop_height, height)
            
            # Add some overlap for better context at boundaries (10% of crop height)
            overlap = int(crop_height * 0.1)
            if i > 0:
                start_y = max(0, start_y - overlap)
            if i < num_crops - 1:
                end_y = min(height, end_y + overlap)
            
            # Crop the image
            cropped_img = img.crop((0, start_y, width, end_y))
            cropped_images.append(cropped_img)
            
            logger.info(f"Created crop {i+1}/{num_crops}: y={start_y}-{end_y}, size={cropped_img.size}")
        
        return cropped_images
    
    def _extract_text_from_crops(
        self,
        crops: List[Image.Image],
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Extract text from multiple cropped images and combine results.
        
        Args:
            crops: List of cropped PIL Image objects
            prompt: OCR prompt
            max_tokens: Maximum tokens per crop
            temperature: Sampling temperature
            
        Returns:
            Combined extracted text
        """
        all_text = []
        
        for i, crop in enumerate(crops):
            logger.info(f"Processing crop {i+1}/{len(crops)}")
            
            try:
                # Encode crop to base64
                crop_b64 = self._encode_image(crop)
                
                # Prepare request payload
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "images": [crop_b64],
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                
                # Make request to Ollama API
                response = requests.post(
                    self.ocr_url,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Extract text from this crop
                result = response.json()
                crop_text = result.get('response', '').strip()
                
                if crop_text:
                    all_text.append(f"--- Section {i+1} ---\n{crop_text}")
                    logger.info(f"Extracted {len(crop_text)} characters from crop {i+1}")
                else:
                    logger.warning(f"No text extracted from crop {i+1}")
                
            except Exception as e:
                logger.error(f"Error processing crop {i+1}: {e}")
                continue
        
        return "\n\n".join(all_text)
    
    def extract_text(
        self,
        image: Union[str, Path, bytes, Image.Image],
        prompt: str = "Extract all text from this image.",
        max_tokens: int = 2048,
        temperature: float = 0.0,
        auto_crop: bool = False
    ) -> str:
        """Extract text from image using DeepSeek OCR.
        
        Args:
            image: Image file path, bytes, or PIL Image object
            prompt: Custom prompt for OCR (default: plain text extraction)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            auto_crop: Whether to automatically crop tall images
            
        Returns:
            Extracted text content
        """
        try:
            # If auto_crop is enabled, check if we need to crop the image
            if auto_crop:
                crops = self._crop_tall_image(image)
                
                if len(crops) > 1:
                    logger.info(f"Processing {len(crops)} cropped images")
                    return self._extract_text_from_crops(crops, prompt, max_tokens, temperature)
            
            # Single image processing (original logic)
            image_b64 = self._encode_image(image)
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Make request to Ollama API
            response = requests.post(
                self.ocr_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Extract and return text
            result = response.json()
            extracted_text = result.get('response', '')
            
            if not extracted_text:
                logger.warning("No text extracted from image")
                return ""
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters")
            return extracted_text.strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama API: {e}")
            raise ConnectionError(f"Cannot connect to Ollama at {self.api_url}: {e}")
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise
    
    def extract_structured_text(
        self,
        image: Union[str, Path, bytes, Image.Image],
        output_format: str = "markdown",
        auto_crop: bool = False
    ) -> str:
        """Extract structured text from image.
        
        Args:
            image: Image file path, bytes, or PIL Image object
            output_format: Output format ('markdown', 'plain', 'html')
            auto_crop: Whether to automatically crop tall images
            
        Returns:
            Structured extracted text
        """
        prompts = {
            "markdown": "Convert this document to markdown format, preserving structure, headings, lists, and tables.",
            "plain": "Extract all text content in plain format, removing formatting.",
            "html": "Extract the content and convert to HTML format, preserving structure and layout."
        }
        
        prompt = prompts.get(output_format.lower(), prompts["markdown"])
        return self.extract_text(image, prompt=prompt, auto_crop=auto_crop)
    
    def extract_tables(self, image: Union[str, Path, bytes, Image.Image], auto_crop: bool = False) -> str:
        """Extract tables from image as HTML.
        
        Args:
            image: Image file path, bytes, or PIL Image object
            auto_crop: Whether to automatically crop tall images
            
        Returns:
            HTML tables from image
        """
        prompt = "Parse all tables and charts in this image. Extract data as HTML tables."
        return self.extract_text(image, prompt=prompt, auto_crop=auto_crop)
    
    def check_connection(self) -> bool:
        """Check if Ollama API is accessible and DeepSeek OCR is available.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            # Check if DeepSeek OCR model is available
            available = any(self.model.lower() in name.lower() for name in model_names)
            
            if not available:
                logger.warning(f"DeepSeek OCR model '{self.model}' not found. Available models: {model_names}")
                return False
            
            logger.info(f"Successfully connected to Ollama with model '{self.model}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API: {e}")
            return False


# Global instance for convenience
_ocr_instance: Optional[DeepSeekOCR] = None


def get_ocr_client(
    api_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr"
) -> DeepSeekOCR:
    """Get or create OCR client instance.
    
    Args:
        api_url: Ollama API URL
        model: DeepSeek OCR model name
        
    Returns:
        DeepSeekOCR instance
    """
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = DeepSeekOCR(api_url=api_url, model=model)
    return _ocr_instance


def extract_text_from_screenshot(
    image_path: Union[str, Path, bytes],
    prompt: str = "Extract all text from this image.",
    api_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    auto_crop: bool = False
) -> str:
    """Convenience function to extract text from screenshot.
    
    Args:
        image_path: Path to screenshot image file or image bytes
        prompt: Custom prompt for OCR extraction
        api_url: Ollama API URL
        model: DeepSeek OCR model name
        auto_crop: Whether to automatically crop tall images
        
    Returns:
        Extracted text content
    """
    ocr = DeepSeekOCR(api_url=api_url, model=model)
    return ocr.extract_text(image_path, prompt=prompt, auto_crop=auto_crop)


def extract_structured_from_screenshot(
    image_path: Union[str, Path, bytes],
    output_format: str = "markdown",
    api_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    auto_crop: bool = False
) -> str:
    """Convenience function to extract structured text from screenshot.
    
    Args:
        image_path: Path to screenshot image file or image bytes
        output_format: Output format ('markdown', 'plain', 'html')
        api_url: Ollama API URL
        model: DeepSeek OCR model name
        auto_crop: Whether to automatically crop tall images
        
    Returns:
        Structured extracted text
    """
    ocr = DeepSeekOCR(api_url=api_url, model=model)
    return ocr.extract_structured_text(image_path, output_format, auto_crop=auto_crop)


def extract_tables_from_screenshot(
    image_path: Union[str, Path, bytes],
    api_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    auto_crop: bool = False
) -> str:
    """Convenience function to extract tables from screenshot.
    
    Args:
        image_path: Path to screenshot image file or image bytes
        api_url: Ollama API URL
        model: DeepSeek OCR model name
        auto_crop: Whether to automatically crop tall images
        
    Returns:
        HTML tables from screenshot
    """
    ocr = DeepSeekOCR(api_url=api_url, model=model)
    return ocr.extract_tables(image_path, auto_crop=auto_crop)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_utils.py <image_path> [output_format]")
        print("Example: python ocr_utils.py screenshot.png markdown")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "plain"
    
    try:
        # Initialize OCR client
        ocr = DeepSeekOCR()
        
        # Check connection
        if not ocr.check_connection():
            print("Failed to connect to Ollama API")
            sys.exit(1)
        
        # Extract text
        if output_format.lower() == "tables":
            result = ocr.extract_tables(image_path)
        else:
            result = ocr.extract_structured_text(image_path, output_format)
        
        print(f"Extracted text ({output_format} format):")
        print("-" * 50)
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)