"""Content filtering using Ollama LLM."""

import ollama
from typing import List
import logging

logger = logging.getLogger(__name__)


class ContentFilter:
    """Filters HTML content using local LLM via Ollama."""
    
    def __init__(self, model: str = "llama3.2", api_url: str = "http://localhost:11434"):
        """Initialize content filter.
        
        Args:
            model: Ollama model name to use
            api_url: Ollama API base URL
        """
        self.model = model
        self.api_url = api_url
        # Set Ollama host if needed
        if api_url != "http://localhost:11434":
            import os
            os.environ["OLLAMA_HOST"] = api_url
    
    def filter_content(self, html: str, topics: List[str]) -> str:
        """Filter HTML content by removing sections related to specified topics.
        
        Args:
            html: Original HTML content
            topics: List of topics to filter out
            
        Returns:
            Filtered HTML with content related to topics removed and fluidly adapted
        """
        if not topics:
            return html
        
        topics_str = ", ".join(f'"{topic}"' for topic in topics)
        
        prompt = f"""You are a web content filter. Your task is to remove any content from the HTML that is related to these topics: {topics_str}.

Instructions:
1. Remove entire paragraphs, sections, divs, or elements that contain content related to any of these topics
2. Maintain the overall structure and flow of the document
3. Ensure the remaining content reads naturally and fluidly
4. Preserve all HTML structure, CSS classes, and formatting
5. Do not add any comments or explanations - only return the modified HTML
6. If a section header is removed, ensure the document flow still makes sense

Return ONLY the modified HTML, nothing else.

HTML to filter:
{html}"""
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt
            )
            
            if not response or 'response' not in response:
                logger.warning("Ollama returned empty or invalid response, using original HTML")
                return html
            
            filtered_html = response['response'].strip()
            
            # Validate that we got actual HTML back (not an error message)
            if not filtered_html or len(filtered_html) < 50:
                logger.warning("Ollama returned suspiciously short response, using original HTML")
                return html
            
            # Remove any markdown code blocks if present
            if filtered_html.startswith("```"):
                lines = filtered_html.split("\n")
                # Remove first line (```html or ```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line (```)
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                filtered_html = "\n".join(lines)
            
            return filtered_html
        except ConnectionError as e:
            logger.error(f"Could not connect to Ollama at {self.api_url}: {e}")
            raise RuntimeError(f"Ollama connection failed. Make sure Ollama is running at {self.api_url}")
        except Exception as e:
            logger.error(f"Error filtering content with Ollama: {e}", exc_info=True)
            # Return original HTML on error to allow browsing to continue
            raise RuntimeError(f"Content filtering failed: {str(e)}")
    
    def check_ollama_available(self) -> bool:
        """Check if Ollama is available and the model exists.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            # Try to list models to check if Ollama is running
            ollama.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

