"""Epollo Pipeline - Node-based pipeline system for news extraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

from epollo.config import Config

logger = logging.getLogger(__name__)


@dataclass
class NodeResult:
    """Result from a node execution."""
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Node(ABC):
    """Base class for pipeline nodes."""
    
    name: str = "base_node"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize node with optional config.
        
        Args:
            config: Node-specific configuration dict
        """
        self.config = config or {}
        self._output_dir: Optional[Path] = None
    
    @property
    def output_dir(self) -> Optional[Path]:
        return self._output_dir
    
    @output_dir.setter
    def output_dir(self, path: Path):
        self._output_dir = path
    
    @abstractmethod
    def process(self, input_data: Any) -> NodeResult:
        """Process input and return result.
        
        Args:
            input_data: Data from previous node or initial input
            
        Returns:
            NodeResult with processed data
        """
        pass
    
    def run(self, input_data: Any) -> NodeResult:
        """Run the node with error handling.
        
        Args:
            input_data: Input data
            
        Returns:
            NodeResult
        """
        try:
            logger.info(f"Running node: {self.name}")
            result = self.process(input_data)
            logger.info(f"Node {self.name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Node {self.name} failed: {e}")
            return NodeResult(data=None, error=str(e))


class Pipeline:
    """Pipeline that executes nodes sequentially."""
    
    def __init__(self, name: str = "epollo_pipeline"):
        """Initialize pipeline.
        
        Args:
            name: Pipeline name for logging
        """
        self.name = name
        self.nodes: List[Node] = []
        self.results: List[NodeResult] = []
    
    def add_node(self, node: Node) -> "Pipeline":
        """Add a node to the pipeline.
        
        Args:
            node: Node to add
            
        Returns:
            Self for chaining
        """
        self.nodes.append(node)
        return self
    
    def run(self, initial_input: Any) -> NodeResult:
        """Run the pipeline.
        
        Args:
            initial_input: Initial input for first node
            
        Returns:
            Final NodeResult from last node
            
        Raises:
            RuntimeError: If any node fails and stop_on_error is True
        """
        logger.info(f"Starting pipeline: {self.name}")
        
        current_input = initial_input
        self.results = []
        
        for i, node in enumerate(self.nodes):
            logger.info(f"Running node {i+1}/{len(self.nodes)}: {node.name}")
            
            result = node.run(current_input)
            self.results.append(result)
            
            if result.error:
                logger.error(f"Pipeline stopped at node {node.name}: {result.error}")
                return result
            
            current_input = result.data
        
        logger.info(f"Pipeline {self.name} completed successfully")
        return self.results[-1] if self.results else NodeResult(data=None)


class PipelineBuilder:
    """Build pipeline from configuration."""
    
    def __init__(self, config: Config):
        """Initialize builder with config.
        
        Args:
            config: Epollo Config object
        """
        self.config = config
    
    def build(self) -> Pipeline:
        """Build pipeline from config.
        
        Returns:
            Configured Pipeline
        """
        from epollo.pipeline.nodes import (
            ScreenshotNode, TileNode, VLNode, SummarizeNode
        )
        
        pipeline = Pipeline("epollo_news_pipeline")
        
        pipeline_config = self.config._config.get("pipeline", {})
        
        if pipeline_config.get("screenshot", {}).get("enabled", True):
            screenshot_config = pipeline_config.get("screenshot", {})
            pipeline.add_node(ScreenshotNode(screenshot_config))
        
        if pipeline_config.get("tile", {}).get("enabled", True):
            tile_config = pipeline_config.get("tile", {})
            pipeline.add_node(TileNode(tile_config))
        
        if pipeline_config.get("vlm", {}).get("enabled", True):
            vlm_config = pipeline_config.get("vlm", {})
            pipeline.add_node(VLNode(vlm_config))
        
        if pipeline_config.get("summarize", {}).get("enabled", True):
            summarize_config = pipeline_config.get("summarize", {})
            pipeline.add_node(SummarizeNode(summarize_config))
        
        return pipeline
    
    def build_from_list(self, node_names: List[str]) -> Pipeline:
        """Build pipeline from list of node names.
        
        Args:
            node_names: List of node names in order
            
        Returns:
            Configured Pipeline
        """
        from epollo.pipeline.nodes import (
            ScreenshotNode, TileNode, VLNode, SummarizeNode
        )
        
        NODE_MAP = {
            "screenshot": ScreenshotNode,
            "tile": TileNode,
            "vlm": VLNode,
            "summarize": SummarizeNode,
        }
        
        pipeline = Pipeline("custom_pipeline")
        
        for name in node_names:
            if name in NODE_MAP:
                config = self.config._config.get("pipeline", {}).get(name, {})
                pipeline.add_node(NODE_MAP[name](config))
        
        return pipeline


def run(url: str, config: Optional[Config] = None) -> str:
    """Run the complete pipeline with default config.
    
    Args:
        url: URL to process
        config: Optional Config object (loads default if not provided)
        
    Returns:
        Final cleaned news text
    """
    if config is None:
        config = Config()
    
    builder = PipelineBuilder(config)
    pipeline = builder.build()
    
    result = pipeline.run(url)
    
    if result.error:
        raise RuntimeError(f"Pipeline failed: {result.error}")
    
    return result.data
