#!/usr/bin/env python3
import plistlib
import os
from pathlib import Path

SCRIPT_PATH = os.path.expandvars("/Users/$USER/Documents/GitHub/epollo/run_screenshots.py")
PLIST_PATH = Path.home() / "Library/LaunchAgents/com.epollo.screenshot.plist"

URLS = [
    "https://news.ycombinator.com",
]

plist = {
    "Label": "com.epollo.screenshot",
    "ProgramArguments": [
        os.path.expandvars("/Users/$USER/Documents/GitHub/epollo/venv/bin/python"),
        SCRIPT_PATH,
    ],
    "StartInterval": 1800,
    "StandardOutPath": "/tmp/epollo_screenshot.log",
    "StandardErrorPath": "/tmp/epollo_screenshot.error.log",
}

PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(PLIST_PATH, "wb") as f:
    plistlib.dump(plist, f)

print(f"Created plist at: {PLIST_PATH}")
print(f"Run: launchctl load {PLIST_PATH}")
