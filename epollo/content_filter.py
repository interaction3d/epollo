"""Content filtering using OpenAI."""

from typing import List

from .openai_client import OpenAIService


class ContentFilter:
    def __init__(self, model: str = "gpt-4.1-mini"):
        self.service = OpenAIService(model=model)

    def filter_content(self, html: str, topics: List[str]) -> str:
        if not topics:
            return html
        topics_str = ", ".join(f'"{t}"' for t in topics)
        prompt = f"""You are an HTML editor.
Remove content related to these topics: {topics_str}.
Return only valid HTML. Preserve structure and readability.

HTML:
{html}
"""
        out = self.service.generate_text(prompt)
        return out if out else html
