#!/usr/bin/env python3
"""Summarize messy markdown into a clean news list using OpenAI."""

import sys
import argparse
from pathlib import Path

from epollo.config import Config
from epollo.openai_client import OpenAIService


def summarize(markdown: str) -> str:
    config = Config()
    service = OpenAIService(model=config.openai_model)
    prompt = f"""Extract only real news items from this text.
Remove ads, promotional content, signup prompts, and social links.
Return numbered list with Title, Summary (1-2 sentences), and Source.

Text:
{markdown}
"""
    return service.generate_text(prompt, temperature=0.2)


def main():
    parser = argparse.ArgumentParser(description="Summarize markdown into clean news list")
    parser.add_argument("input", nargs="?", help="Input markdown file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    markdown = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
    if not markdown.strip():
        print("Error: No input provided", file=sys.stderr)
        sys.exit(1)

    result = summarize(markdown)
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Saved to: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
