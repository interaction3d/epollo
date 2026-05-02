"""Configuration management for Epollo browser."""

from pathlib import Path
from typing import Any, Dict, List

import yaml


class Config:
    DEFAULT_CONFIG = {
        "topics": ["advertising", "sponsored content", "newsletter signup"],
        "openai": {"model": "gpt-4.1-mini"},
        "filtering": {"enabled": True},
        "display": {"remove_images": False, "summary_view": False},
    }

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        merged = {
            "topics": list(self.DEFAULT_CONFIG["topics"]),
            "openai": dict(self.DEFAULT_CONFIG["openai"]),
            "filtering": dict(self.DEFAULT_CONFIG["filtering"]),
            "display": dict(self.DEFAULT_CONFIG["display"]),
        }
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            merged.update({k: v for k, v in config.items() if k not in {"openai", "filtering", "display"}})
            for key in ("openai", "filtering", "display"):
                if key in config and isinstance(config[key], dict):
                    merged[key].update(config[key])
        return merged

    @property
    def topics(self) -> List[str]:
        return self._config.get("topics", [])

    @property
    def openai_model(self) -> str:
        return self._config.get("openai", {}).get("model", "gpt-4.1-mini")

    @property
    def filtering_enabled(self) -> bool:
        return self._config.get("filtering", {}).get("enabled", True)

    @property
    def remove_images(self) -> bool:
        return self._config.get("display", {}).get("remove_images", False)

    @property
    def summary_view(self) -> bool:
        return self._config.get("display", {}).get("summary_view", False)

    def reload(self):
        self._config = self._load_config()
