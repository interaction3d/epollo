"""OCR utilities using OpenAI vision."""

from pathlib import Path
from typing import Union

from .openai_client import OpenAIService


class OCRClient:
    def __init__(self, model: str = "gpt-4.1-mini"):
        self.service = OpenAIService(model=model)

    def extract_text(self, image: Union[str, Path, bytes], prompt: str = "Extract all readable text.") -> str:
        return self.service.generate_from_image(image, prompt)
