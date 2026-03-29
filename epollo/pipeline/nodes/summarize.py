"""Summarize node for pipeline."""

from typing import Any, Dict, Optional
import logging

from epollo.pipeline import Node, NodeResult
from epollo.summarize import summarize as summarize_text

logger = logging.getLogger(__name__)


class SummarizeNode(Node):
    """Node that cleans and summarizes text using LLM."""
    
    name = "summarize"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize summarize node.
        
        Args:
            config: Node config (currently unused, uses summarize defaults)
        """
        super().__init__(config)
    
    def process(self, input_data: Any) -> NodeResult:
        """Summarize and clean text.
        
        Args:
            input_data: Raw text to summarize
            
        Returns:
            NodeResult with cleaned text
        """
        text = input_data
        
        if not isinstance(text, str):
            return NodeResult(
                data=None,
                error=f"Expected text string, got {type(text)}"
            )
        
        if not text.strip():
            return NodeResult(
                data=None,
                error="Empty text input"
            )
        
        logger.info(f"Summarizing text ({len(text)} chars)")
        
        try:
            cleaned_text = summarize_text(text)
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return NodeResult(data=None, error=str(e))
        
        return NodeResult(
            data=cleaned_text,
            metadata={
                "input_length": len(text),
                "output_length": len(cleaned_text)
            }
        )
