"""Shared OpenAI client helpers for Epollo."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional, Union

from openai import OpenAI


ImageLike = Union[str, Path, bytes]


class OpenAIService:
    """Small wrapper around OpenAI SDK used by filtering/OCR/summarization."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Export it before running Epollo.")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    @staticmethod
    def _encode_image(image: ImageLike) -> str:
        if isinstance(image, (str, Path)):
            data = Path(image).read_bytes()
        elif isinstance(image, bytes):
            data = image
        else:
            raise ValueError("image must be file path or bytes")
        return base64.b64encode(data).decode("utf-8")

    def generate_text(self, prompt: str, temperature: float = 0.2) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature,
        )
        return response.output_text.strip()

    def generate_from_image(self, image: ImageLike, prompt: str) -> str:
        image_b64 = self._encode_image(image)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": f"data:image/png;base64,{image_b64}"},
                    ],
                }
            ],
        )
        return response.output_text.strip()
