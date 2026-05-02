"""Vision-language utilities via OpenAI."""

from pathlib import Path
from typing import Union

from .openai_client import OpenAIService


class VisionClient:
    def __init__(self, model: str = "gpt-4.1-mini"):
        self.service = OpenAIService(model=model)

    def query(self, image: Union[str, Path, bytes], prompt: str) -> str:
        return self.service.generate_from_image(image, prompt)

    def extract_headlines(self, image: Union[str, Path, bytes]) -> str:
        return self.query(image, "Extract news headlines and short summaries.")
