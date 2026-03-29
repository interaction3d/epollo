"""Screenshot node for pipeline."""

from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime
import logging

from epollo.pipeline import Node, NodeResult
from epollo.browser import take_url_screenshot

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("data/screenshots")


class ScreenshotNode(Node):
    """Node that captures screenshots from URLs."""
    
    name = "screenshot"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize screenshot node.
        
        Args:
            config: Node config with keys:
                - width: Image width (default: 768)
                - height: Image height (default: 2048)
                - full_page: Capture full page (default: True)
                - output_dir: Output directory (default: data/screenshots)
        """
        super().__init__(config)
        self.width = self.config.get("width", 768)
        self.height = self.config.get("height", 2048)
        self.full_page = self.config.get("full_page", True)
        output_dir = self.config.get("output_dir", DEFAULT_OUTPUT_DIR)
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, input_data: Any) -> NodeResult:
        """Take screenshot of URL.
        
        Args:
            input_data: URL string
            
        Returns:
            NodeResult with screenshot file path
        """
        url = input_data
        if not isinstance(url, str):
            return NodeResult(
                data=None,
                error=f"Expected URL string, got {type(url)}"
            )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = hash(url) % 10000
        filename = f"screenshot_{timestamp}_{url_hash}.png"
        output_path = self._output_dir / filename
        
        logger.info(f"Taking screenshot of {url}")
        
        screenshot_bytes = take_url_screenshot(
            url=url,
            output_path=str(output_path),
            width=self.width,
            height=self.height,
            full_page=self.full_page
        )
        
        return NodeResult(
            data=str(output_path),
            metadata={
                "url": url,
                "width": self.width,
                "height": self.height,
                "size_bytes": len(screenshot_bytes)
            }
        )
