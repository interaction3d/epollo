"""VLM utility functions using Qwen3-VL via Ollama API."""

import base64
import logging
from typing import Optional, Union
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded image string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class Qwen3VL:
    """Qwen3-VL client using Ollama API."""
    
    def __init__(
        self,
        api_url: str = "http://localhost:11434",
        model: str = "qwen3-vl:2b",
        timeout: int = 120
    ):
        """Initialize Qwen3-VL client.
        
        Args:
            api_url: Ollama API base URL
            model: Model name for Qwen3-VL
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.vlm_url = f"{self.api_url}/api/generate"
    
    def _encode_image(self, image: Union[str, Path, bytes]) -> str:
        """Encode image to base64 string.
        
        Args:
            image: Path to image file or image bytes
            
        Returns:
            Base64 encoded image string
        """
        if isinstance(image, (str, Path)):
            with open(image, 'rb') as f:
                image_bytes = f.read()
        elif isinstance(image, bytes):
            image_bytes = image
        else:
            raise ValueError("image must be file path or bytes")
        
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def query(
        self,
        image: Union[str, Path, bytes],
        prompt: str = "Please read the image and extract the content",
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        """Query the VLM model with an image and prompt.
        
        Args:
            image: Path to the image file or image bytes
            prompt: The prompt to send to the model
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            The model's response text
        """
        image_b64 = self._encode_image(image)
        
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
        
        response = requests.post(self.vlm_url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def extract_headlines(self, image: Union[str, Path, bytes]) -> str:
        """Extract news headlines from an image.
        
        Args:
            image: Path to the image file or image bytes
            
        Returns:
            Extracted headlines
        """
        prompt = "Please read the image and extract news content"
        return self.query(image, prompt)
    
    def check_connection(self) -> bool:
        """Check if Ollama API is accessible and Qwen3-VL is available.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            available = any(self.model.lower() in name.lower() for name in model_names)
            
            if not available:
                logger.warning(f"Qwen3-VL model '{self.model}' not found. Available models: {model_names}")
                return False
            
            logger.info(f"Successfully connected to Ollama with model '{self.model}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API: {e}")
            return False


def query_vlm(
    image_path: str,
    prompt: str = "Please read the image and extract content",
    model: str = "qwen3-vl:2b",
    api_url: str = "http://localhost:11434"
) -> str:
    """Query the VLM model with an image and prompt.
    
    Args:
        image_path: Path to the image file
        prompt: The prompt to send to the model
        model: The VLM model to use
        api_url: Ollama API base URL
        
    Returns:
        The model's response text
    """
    vlm = Qwen3VL(api_url=api_url, model=model)
    return vlm.query(image_path, prompt)


def extract_headlines(
    image_path: str,
    model: str = "qwen3-vl:2b",
    api_url: str = "http://localhost:11434"
) -> str:
    """Extract news headlines from an image.
    
    Args:
        image_path: Path to the image file
        model: The VLM model to use
        api_url: Ollama API base URL
        
    Returns:
        Extracted headlines
    """
    vlm = Qwen3VL(api_url=api_url, model=model)
    return vlm.extract_headlines(image_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vlm_utils.py <image_path> [prompt]")
        print("Example: python vlm_utils.py screenshot.png 'Extract news headlines'")
        sys.exit(1)
    
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Please read the image and extract content"
    
    try:
        vlm = Qwen3VL()
        
        if not vlm.check_connection():
            print("Failed to connect to Ollama API")
            sys.exit(1)
        
        result = vlm.query(image_path, prompt)
        
        print(f"VLM Response:")
        print("-" * 50)
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
