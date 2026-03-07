"""Tile node for pipeline."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

from epollo.pipeline import Node, NodeResult
from epollo.screenshot import crop_to_square_tiles

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("data/tiles")


class TileNode(Node):
    """Node that crops screenshot into tiles."""
    
    name = "tile"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize tile node.
        
        Args:
            config: Node config with keys:
                - overlap: Overlap ratio 0-1 (default: 0.3)
                - output_dir: Output directory (default: data/tiles)
        """
        super().__init__(config)
        self.overlap = self.config.get("overlap", 0.3)
        self._output_dir = Path(self.config.get("output_dir", DEFAULT_OUTPUT_DIR))
        self._output_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, input_data: Any) -> NodeResult:
        """Crop screenshot into tiles.
        
        Args:
            input_data: Screenshot file path string
            
        Returns:
            NodeResult with list of tile file paths
        """
        screenshot_path = input_data
        if not isinstance(screenshot_path, str):
            return NodeResult(
                data=None,
                error=f"Expected screenshot path string, got {type(screenshot_path)}"
            )
        
        if not Path(screenshot_path).exists():
            return NodeResult(
                data=None,
                error=f"Screenshot not found: {screenshot_path}"
            )
        
        logger.info(f"Cropping {screenshot_path} into tiles")
        
        tile_paths = crop_to_square_tiles(
            image_path=screenshot_path,
            output_dir=str(self._output_dir),
            overlap=self.overlap
        )
        
        return NodeResult(
            data=tile_paths,
            metadata={
                "screenshot_path": screenshot_path,
                "num_tiles": len(tile_paths),
                "overlap": self.overlap
            }
        )
