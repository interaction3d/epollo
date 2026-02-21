#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from epollo.browser import take_url_screenshot

URLS = [
    "https://example.com",
    "https://news.ycombinator.com",
]

OUTPUT_DIR = Path(__file__).parent / "screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)

date_prefix = datetime.now().strftime("%Y%m%d")

for i, url in enumerate(URLS):
    output_path = OUTPUT_DIR / f"{date_prefix}_screenshot_{i}_{url.replace('https://', '').replace('/', '_')}.png"
    take_url_screenshot(url, output_path=str(output_path))
    print(f"Saved: {output_path}")
