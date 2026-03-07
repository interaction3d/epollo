"""VLM node for pipeline."""

from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

from epollo.pipeline import Node, NodeResult
from epollo.vlm_utils import Qwen3VL
from epollo.config import Config

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = "Please read this image and extract news content"


class VLNode(Node):
    """Node that extracts text from image tiles using VLM."""
    
    name = "vlm"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize VLM node.
        
        Args:
            config: Node config with keys:
                - prompt: Prompt for VLM (default: extract news content)
                - model: VLM model name (default: qwen3-vl:2b)
                - api_url: Ollama API URL
        """
        super().__init__(config)
        
        epollo_config = Config()
        
        self.prompt = self.config.get("prompt", DEFAULT_PROMPT)
        # Default to qwen3-vl:2b (vision model) if not specified
        self.model = self.config.get("model", "qwen3-vl:2b")
        self.api_url = self.config.get("api_url", epollo_config.ollama_api_url)
        
        self.vlm = Qwen3VL(
            model=self.model,
            api_url=self.api_url
        )
    
    def process(self, input_data: Any) -> NodeResult:
        """Extract text from image tiles using VLM.
        
        Args:
            input_data: List of tile file paths or single tile path
            
        Returns:
            NodeResult with extracted text
        """
        tile_paths = input_data
        
        if isinstance(tile_paths, str):
            tile_paths = [tile_paths]
        
        if not isinstance(tile_paths, list):
            return NodeResult(
                data=None,
                error=f"Expected list of tile paths, got {type(tile_paths)}"
            )
        
        logger.info(f"Extracting text from {len(tile_paths)} tiles")
        
        all_text = []
        for i, tile_path in enumerate(tile_paths):
            if not Path(tile_path).exists():
                logger.warning(f"Tile not found: {tile_path}")
                continue
            
            logger.info(f"Processing tile {i+1}/{len(tile_paths)}: {tile_path}")
            
            try:
                text = self.vlm.query(tile_path, self.prompt)
                all_text.append(text)
            except Exception as e:
                logger.error(f"Error processing tile {tile_path}: {e}")
                continue
        
        if not all_text:
            return NodeResult(
                data=None,
                error="No text extracted from any tile"
            )
        
        combined_text = "\n".join(all_text)
        
        return NodeResult(
            data=combined_text,
            metadata={
                "num_tiles_processed": len(all_text),
                "model": self.model,
                "prompt": self.prompt
            }
        )
