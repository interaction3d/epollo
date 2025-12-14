"""Main entry point for Epollo browser."""

import sys
import logging
from pathlib import Path
from .browser import Browser
from .config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    # Load configuration
    config_path = Path("config.yaml")
    if not config_path.exists():
        # Try to find config in current directory or parent
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    config = Config(str(config_path))
    
    # Create and start browser
    browser = Browser(config)
    browser.create_window()


if __name__ == "__main__":
    main()

