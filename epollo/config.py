"""Configuration management for Epollo browser."""

import os
import yaml
from typing import List, Dict, Any
from pathlib import Path


class Config:
    """Manages application configuration from YAML file."""
    
    DEFAULT_CONFIG = {
        "topics": [
            "advertising",
            "sponsored content",
            "newsletter signup"
        ],
        "ollama": {
            "model": "qwen2.5:1.5b",
            "api_url": "http://localhost:11434"
        },
        "filtering": {
            "enabled": True
        },
        "display": {
            "remove_images": False,
            "summary_view": False
        }
    }
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # Merge with defaults to ensure all keys exist
                    merged = self.DEFAULT_CONFIG.copy()
                    if config:
                        merged.update(config)
                        # Deep merge for nested dicts
                        if "ollama" in config:
                            merged["ollama"].update(config["ollama"])
                        if "filtering" in config:
                            merged["filtering"].update(config["filtering"])
                        if "display" in config:
                            merged["display"].update(config["display"])
                    return merged
            except (yaml.YAMLError, IOError) as e:
                print(f"Warning: Failed to load config file: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()
    
    @property
    def topics(self) -> List[str]:
        """Get list of topics to filter."""
        return self._config.get("topics", [])
    
    @property
    def ollama_model(self) -> str:
        """Get Ollama model name."""
        return self._config.get("ollama", {}).get("model", "llama3.2")
    
    @property
    def ollama_api_url(self) -> str:
        """Get Ollama API URL."""
        return self._config.get("ollama", {}).get("api_url", "http://localhost:11434")
    
    @property
    def filtering_enabled(self) -> bool:
        """Check if filtering is enabled by default."""
        return self._config.get("filtering", {}).get("enabled", True)
    
    @property
    def remove_images(self) -> bool:
        """Check if images should be removed from rendered pages."""
        return self._config.get("display", {}).get("remove_images", False)
    
    @property
    def summary_view(self) -> bool:
        """Check if summary view should be used instead of full page."""
        return self._config.get("display", {}).get("summary_view", False)
    
    def reload(self):
        """Reload configuration from file."""
        self._config = self._load_config()

