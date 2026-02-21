#!/usr/bin/env python3
import plistlib
import os
from pathlib import Path

SCRIPT_PATH = "/Users/tylerzhu/Documents/GitHub/epollo/run_screenshots.py"
PLIST_PATH = Path.home() / "Library/LaunchAgents/com.epollo.screenshot.plist"

URLS = [
    "https://example.com",
    "https://news.ycombinator.com",
]

plist = {
    "Label": "com.epollo.screenshot",
    "ProgramArguments": [
        "/Users/tylerzhu/Documents/GitHub/epollo/venv/bin/python",
        SCRIPT_PATH,
    ],
    "StartCalendarInterval": {
        "Hour": 10,
        "Minute": 0,
    },
    "StandardOutPath": "/tmp/epollo_screenshot.log",
    "StandardErrorPath": "/tmp/epollo_screenshot.error.log",
}

PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(PLIST_PATH, "wb") as f:
    plistlib.dump(plist, f)

print(f"Created plist at: {PLIST_PATH}")
print(f"Run: launchctl load {PLIST_PATH}")
