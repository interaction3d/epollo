#!/usr/bin/env python3
"""Summarize messy markdown into a clean news list using Ollama."""

import sys
import argparse
from pathlib import Path


def summarize(markdown: str) -> str:
    """Clean messy markdown into a news list using Ollama.
    
    Args:
        markdown: Messy markdown content to clean
        
    Returns:
        Cleaned news list as string
    """
    from epollo.config import Config
    import ollama
    
    config = Config()
    
    prompt = f"""Extract ONLY real news articles from the text below. 

REMOVE these completely:
- Advertisements, ads, sponsored content
- Promotional content, "Buy now" messages
- Newsletter signup prompts
- Social media links and follow buttons
- Footer links, sidebar content

Format as a clean numbered list:
1. Title: [headline]
2. Summary: [1-2 sentence summary]
3. Source: [source name and date if available]

Skip anything that is not a real news article.

Text:
{markdown}

Output:"""

    try:
        response = ollama.generate(
            model=config.ollama_model,
            prompt=prompt,
            options={"temperature": 0.3, "top_p": 0.9}
        )
        
        if response and 'response' in response:
            result = response['response'].strip()
            
            filtered_lines = [
                line for line in result.split('\n')
                if not any(word in line.lower() for word in ['advertisement', 'ad:', 'sponsored', 'promotion', 'buy now', 'subscribe', 'newsletter', 'follow us', 'social'])
            ]
            
            result = '\n'.join(filtered_lines)
            return result if result.strip() else "No news content found."
        return "Error: Empty response from Ollama"
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Summarize markdown into clean news list")
    parser.add_argument("input", nargs="?", help="Input markdown file (default: stdin)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    if args.input:
        markdown = Path(args.input).read_text(encoding="utf-8")
    else:
        markdown = sys.stdin.read()
    
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
