"""Epollo - A lightweight Python browser with LLM-based content filtering."""

from epollo.pipeline import Pipeline, PipelineBuilder, run
from epollo.pipeline.nodes import (
    ScreenshotNode,
    TileNode,
    VLNode,
    SummarizeNode,
)

__version__ = "0.1.0"

__all__ = [
    "Pipeline",
    "PipelineBuilder", 
    "run",
    "ScreenshotNode",
    "TileNode",
    "VLNode",
    "SummarizeNode",
]
