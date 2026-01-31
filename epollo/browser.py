"""Main browser window implementation."""

import webview
import threading
import requests
from urllib.parse import urlparse, urljoin
from typing import Optional, List, Dict, Tuple
import logging
import re
from html.parser import HTMLParser
from html import unescape
import ollama
from .config import Config
from .content_filter import ContentFilter
from .screenshot import render_html_to_screenshot_sync, render_url_to_screenshot_sync

logger = logging.getLogger(__name__)


class BrowserAPI:
    """API class for JavaScript to call Python methods."""
    
    def __init__(self, browser_instance):
        """Initialize with browser instance.
        
        Args:
            browser_instance: Browser instance to delegate to
        """
        self._browser = browser_instance
    
    def navigate(self, url: str, use_filter: bool = False):
        """Navigate to URL - called from JavaScript.
        
        Args:
            url: URL to navigate to
            use_filter: Whether to apply content filtering
        """
        self._browser.navigate(url, use_filter)
    
    def take_screenshot(self, filename: str = "screenshot.png", width: int = 1200, height: int = 800):
        """Take a screenshot of the current page - called from JavaScript.
        
        Args:
            filename: Screenshot filename
            width: Image width
            height: Image height
        """
        try:
            # Create screenshots directory if it doesn't exist
            import os
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            output_path = os.path.join(screenshots_dir, filename)
            self._browser.take_screenshot(output_path=output_path, width=width, height=height)
            return f"Screenshot saved to {output_path}"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"


class Browser:
    """Lightweight browser with content filtering capability."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize browser.
        
        Args:
            config: Configuration instance (creates default if None)
        """
        self.config = config or Config()
        self.filtering_enabled = self.config.filtering_enabled
        self.window = None
        self.current_url = ""
        self._html_content = None
        
        # Initialize content filter only if filtering is enabled and topics are configured
        if self.filtering_enabled and self.config.topics:
            self.content_filter = ContentFilter(
                model=self.config.ollama_model,
                api_url=self.config.ollama_api_url
            )
            # Check Ollama availability
            if not self.content_filter.check_ollama_available():
                logger.warning(
                    f"Ollama is not available at {self.config.ollama_api_url}. "
                    "Content filtering will not work. Make sure Ollama is running."
                )
        else:
            self.content_filter = None
    
    def _create_html_ui(self) -> str:
        """Create HTML UI with URL bar and filter toggle."""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Courier New', Courier, monospace;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
            background: #fafafa;
            color: #333;
        }
        .toolbar {
            background: #fff;
            border-bottom: 2px solid #333;
            padding: 16px;
            display: flex;
            gap: 16px;
            align-items: center;
            flex-shrink: 0;
        }
        #url-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #333;
            background: #fff;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            outline: none;
            transition: all 0.2s ease;
        }
        #url-input:focus {
            background: #f0f0f0;
            border-color: #000;
        }
        #filter-toggle {
            padding: 12px 20px;
            border: 2px solid #333;
            background: #fff;
            cursor: pointer;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            font-weight: bold;
            white-space: nowrap;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        #filter-toggle:hover {
            background: #f0f0f0;
        }
        #filter-toggle.active {
            background: #333;
            color: #fff;
        }
        #screenshot-btn {
            padding: 12px 20px;
            border: 2px solid #333;
            background: #fff;
            cursor: pointer;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            font-weight: bold;
            white-space: nowrap;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        #screenshot-btn:hover {
            background: #f0f0f0;
        }
        #status {
            padding: 12px 16px;
            font-size: 12px;
            color: #666;
            white-space: nowrap;
            font-family: 'Courier New', Courier, monospace;
            font-style: italic;
            min-width: 200px;
        }
        #content-frame {
            flex: 1;
            border: none;
            width: 100%;
            height: 100%;
            background: #fff;
        }
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            font-size: 16px;
            color: #666;
            font-family: 'Courier New', Courier, monospace;
        }
        
        /* Typewriter cursor effect */
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        #url-input:focus::after {
            content: '_';
            position: absolute;
            animation: blink 1s infinite;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <input type="text" id="url-input" placeholder="ENTER URL..." />
        <button id="filter-toggle">FILTER: OFF</button>
        <button id="screenshot-btn">SCREENSHOT</button>
        <div id="status">READY</div>
    </div>
    <iframe id="content-frame" sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation"></iframe>
    
    <script>
        const urlInput = document.getElementById('url-input');
        const filterToggle = document.getElementById('filter-toggle');
        const screenshotBtn = document.getElementById('screenshot-btn');
        const contentFrame = document.getElementById('content-frame');
        const status = document.getElementById('status');
        
        // URL input handling
        urlInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const url = urlInput.value.trim();
                if (url) {
                    status.textContent = 'LOADING...';
                    window.pywebview.api.navigate(url, filterToggle.classList.contains('active'));
                }
            }
        });
        
        // Filter toggle handling
        filterToggle.addEventListener('click', function() {
            const isActive = filterToggle.classList.contains('active');
            if (isActive) {
                filterToggle.classList.remove('active');
                filterToggle.textContent = 'FILTER: OFF';
            } else {
                filterToggle.classList.add('active');
                filterToggle.textContent = 'FILTER: ON';
            }
            // Reload current page with new filter setting
            const url = urlInput.value.trim();
            if (url) {
                status.textContent = 'RELOADING WITH FILTER ' + (filterToggle.classList.contains('active') ? 'ON' : 'OFF') + '...';
                window.pywebview.api.navigate(url, filterToggle.classList.contains('active'));
            }
        });
        
        // Helper function to update status from Python
        window.updateStatus = function(message) {
            status.textContent = message.toUpperCase();
        };
        
        // Helper function to update URL from Python
        window.updateUrl = function(url) {
            urlInput.value = url;
        };
        
        // Screenshot button handling
        screenshotBtn.addEventListener('click', function() {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            const filename = `screenshot-${timestamp}.png`;
            status.textContent = 'TAKING SCREENSHOT...';
            
            window.pywebview.api.take_screenshot(filename).then(function(result) {
                status.textContent = 'SCREENSHOT TAKEN';
                setTimeout(() => {
                    status.textContent = 'READY';
                }, 2000);
            }).catch(function(error) {
                status.textContent = 'SCREENSHOT FAILED';
                setTimeout(() => {
                    status.textContent = 'READY';
                }, 2000);
            });
        });
    </script>
</body>
</html>
"""
    
    def _fetch_url(self, url: str) -> tuple[str, str]:
        """Fetch content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_content, final_url after redirects)
        """
        try:
            # Validate and normalize URL
            if not url or not url.strip():
                raise ValueError("URL cannot be empty")
            
            # Ensure URL has a scheme
            original_url = url
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Basic URL validation
            try:
                parsed = urlparse(url)
                if not parsed.netloc:
                    raise ValueError(f"Invalid URL: {original_url}")
            except Exception as e:
                raise ValueError(f"Invalid URL format: {original_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True, stream=False)
            response.raise_for_status()
            
            # Get final URL after redirects
            final_url = response.url
            
            # Check content size to avoid loading huge files
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError(f"Content too large ({int(content_length) / 1024 / 1024:.1f}MB). Maximum 10MB supported.")
            
            # Try to get HTML content
            content_type = response.headers.get('Content-Type', '').lower()
            if 'html' in content_type or not content_type:
                return response.text, final_url
            else:
                # If not HTML, wrap it in HTML
                return f'<html><body><pre>{response.text}</pre></body></html>', final_url
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out while loading {url}"
            logger.error(error_msg)
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Courier New', Courier, monospace;
                        padding: 32px;
                        background: #fafafa;
                        color: #333;
                        line-height: 1.8;
                    }}
                    h2 {{
                        font-size: 24px;
                        margin-bottom: 20px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        border-bottom: 3px solid #333;
                        padding-bottom: 10px;
                    }}
                    p {{
                        margin-bottom: 16px;
                        font-size: 14px;
                    }}
                    .error-detail {{
                        color: #666;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <h2>TIMEOUT ERROR</h2>
                <p>COULD NOT LOAD {url}</p>
                <p class="error-detail">THE REQUEST TOOK TOO LONG. PLEASE TRY AGAIN OR CHECK YOUR CONNECTION.</p>
            </body>
            </html>
            """
            return error_html, url
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error while loading {url}"
            logger.error(error_msg)
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Courier New', Courier, monospace;
                        padding: 32px;
                        background: #fafafa;
                        color: #333;
                        line-height: 1.8;
                    }}
                    h2 {{
                        font-size: 24px;
                        margin-bottom: 20px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        border-bottom: 3px solid #333;
                        padding-bottom: 10px;
                    }}
                    p {{
                        margin-bottom: 16px;
                        font-size: 14px;
                    }}
                    .error-detail {{
                        color: #666;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <h2>CONNECTION ERROR</h2>
                <p>COULD NOT CONNECT TO {url}</p>
                <p class="error-detail">PLEASE CHECK YOUR INTERNET CONNECTION AND TRY AGAIN.</p>
            </body>
            </html>
            """
            return error_html, url
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code} while loading {url}"
            logger.error(error_msg)
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Courier New', Courier, monospace;
                        padding: 32px;
                        background: #fafafa;
                        color: #333;
                        line-height: 1.8;
                    }}
                    h2 {{
                        font-size: 24px;
                        margin-bottom: 20px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        border-bottom: 3px solid #333;
                        padding-bottom: 10px;
                    }}
                    p {{
                        margin-bottom: 16px;
                        font-size: 14px;
                    }}
                    .error-detail {{
                        color: #666;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <h2>HTTP ERROR {e.response.status_code}</h2>
                <p>COULD NOT LOAD {url}</p>
                <p class="error-detail">{str(e).upper()}</p>
            </body>
            </html>
            """
            return error_html, url
        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg)
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Courier New', Courier, monospace;
                        padding: 32px;
                        background: #fafafa;
                        color: #333;
                        line-height: 1.8;
                    }}
                    h2 {{
                        font-size: 24px;
                        margin-bottom: 20px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        border-bottom: 3px solid #333;
                        padding-bottom: 10px;
                    }}
                    p {{
                        margin-bottom: 16px;
                        font-size: 14px;
                    }}
                    .error-detail {{
                        color: #666;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <h2>INVALID URL</h2>
                <p class="error-detail">{error_msg.upper()}</p>
            </body>
            </html>
            """
            return error_html, url
        except requests.exceptions.RequestException as e:
            error_msg = f"Error loading {url}: {str(e)}"
            logger.error(error_msg)
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Courier New', Courier, monospace;
                        padding: 32px;
                        background: #fafafa;
                        color: #333;
                        line-height: 1.8;
                    }}
                    h2 {{
                        font-size: 24px;
                        margin-bottom: 20px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        border-bottom: 3px solid #333;
                        padding-bottom: 10px;
                    }}
                    p {{
                        margin-bottom: 16px;
                        font-size: 14px;
                    }}
                    .error-detail {{
                        color: #666;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <h2>ERROR LOADING PAGE</h2>
                <p>COULD NOT LOAD {url}</p>
                <p class="error-detail">{str(e).upper()}</p>
            </body>
            </html>
            """
            return error_html, url
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Courier New', Courier, monospace;
                        padding: 32px;
                        background: #fafafa;
                        color: #333;
                        line-height: 1.8;
                    }}
                    h2 {{
                        font-size: 24px;
                        margin-bottom: 20px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        border-bottom: 3px solid #333;
                        padding-bottom: 10px;
                    }}
                    p {{
                        margin-bottom: 16px;
                        font-size: 14px;
                    }}
                    .error-detail {{
                        color: #666;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <h2>UNEXPECTED ERROR</h2>
                <p>AN UNEXPECTED ERROR OCCURRED WHILE LOADING {url}</p>
                <p class="error-detail">{str(e).upper()}</p>
            </body>
            </html>
            """
            return error_html, url
    
    def _extract_text_content(self, html: str) -> str:
        """Extract plain text content from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Plain text content
        """
        # Remove scripts and styles
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Decode HTML entities
        text = unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _extract_sections(self, html: str) -> List[Dict[str, str]]:
        """Extract sections from HTML (heading + content).
        
        Args:
            html: HTML content
            
        Returns:
            List of dictionaries with 'title' and 'content' keys
        """
        sections = []
        
        # Find all headings (h1-h6) and their following content
        # Pattern: heading tag followed by content until next heading
        pattern = r'<h([1-6])[^>]*>(.*?)</h[1-6]>'
        
        # Extract headings with their positions
        headings = []
        for match in re.finditer(pattern, html, re.IGNORECASE | re.DOTALL):
            level = int(match.group(1))
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            title = unescape(title)
            headings.append({
                'level': level,
                'title': title,
                'start': match.start(),
                'end': match.end()
            })
        
        # Extract content between headings
        for i, heading in enumerate(headings):
            # Determine end position (start of next heading or end of document)
            if i + 1 < len(headings):
                end_pos = headings[i + 1]['start']
            else:
                end_pos = len(html)
            
            # Extract content between heading end and next heading
            content_html = html[heading['end']:end_pos]
            
            # Extract text content
            content_text = self._extract_text_content(content_html)
            
            # Limit content length (we'll take first few paragraphs)
            paragraphs = [p.strip() for p in content_text.split('\n\n') if p.strip()]
            # Take up to 6 lines/paragraphs
            content_preview = '\n\n'.join(paragraphs[:6])
            
            if heading['title'] and content_preview:
                sections.append({
                    'title': heading['title'],
                    'content': content_preview
                })
        
        # If no headings found, try to extract from article/main content
        if not sections:
            # Try to find article or main tag
            article_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.IGNORECASE | re.DOTALL)
            main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.IGNORECASE | re.DOTALL)
            
            content_html = ''
            if article_match:
                content_html = article_match.group(1)
            elif main_match:
                content_html = main_match.group(1)
            else:
                # Fallback to body
                body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL)
                if body_match:
                    content_html = body_match.group(1)
            
            if content_html:
                content_text = self._extract_text_content(content_html)
                paragraphs = [p.strip() for p in content_text.split('\n\n') if p.strip() and len(p.strip()) > 50]
                
                # Create sections from paragraphs (group them)
                for i in range(0, min(len(paragraphs), 5), 2):
                    title = paragraphs[i][:100] + "..." if len(paragraphs[i]) > 100 else paragraphs[i]
                    content = '\n\n'.join(paragraphs[i:i+6])
                    if content:
                        sections.append({
                            'title': title,
                            'content': content
                        })
        
        # Limit to reasonable number of sections
        return sections[:10]
    
    def _generate_summary_bullets(self, title: str, content: str) -> str:
        """Generate summary bullets using Ollama.
        
        Args:
            title: Section title
            content: Section content
            
        Returns:
            Bullet points summary
        """
        prompt = f"""Given the following content section, provide 3-5 concise bullet points summarizing the key information.

Title: {title}

Content:
{content[:2000]}  # Limit content length

Provide only the bullet points, one per line, starting with "- ". Do not include the title or any other text."""

        try:
            response = ollama.generate(
                model=self.config.ollama_model,
                prompt=prompt
            )
            
            if response and 'response' in response:
                bullets = response['response'].strip()
                # Clean up - ensure each line starts with -
                lines = [line.strip() for line in bullets.split('\n') if line.strip()]
                cleaned_bullets = []
                for line in lines:
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        cleaned_bullets.append(line)
                    else:
                        cleaned_bullets.append(f"- {line}")
                return '\n'.join(cleaned_bullets[:5])  # Limit to 5 bullets
            return ""
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""
    
    def _create_summary_html(self, sections: List[Dict[str, str]], url: str) -> str:
        """Create minimalistic HTML page with summaries.
        
        Args:
            sections: List of section dictionaries with title, content, and optionally summary
            url: Original URL
            
        Returns:
            HTML string for summary view
        """
        # Escape the URL for display text only (href needs actual URL)
        escaped_url_display = self._escape_html(url)
        
        html_parts = [f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SUMMARY VIEW</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Courier New', Courier, monospace;
            line-height: 1.8;
            color: #333;
            background: #fafafa;
            padding: 32px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 28px;
            margin-bottom: 40px;
            padding-bottom: 16px;
            border-bottom: 3px solid #333;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .section {{
            margin-bottom: 48px;
            padding: 24px;
            background: #fff;
            border: 2px solid #333;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #000;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary {{
            margin-bottom: 20px;
            padding-left: 0;
        }}
        .summary ul {{
            list-style: none;
            padding: 0;
        }}
        .summary li {{
            margin-bottom: 12px;
            padding-left: 24px;
            position: relative;
            font-size: 14px;
        }}
        .summary li:before {{
            content: ">";
            position: absolute;
            left: 0;
            color: #333;
            font-weight: bold;
        }}
        .original-content {{
            background: #fff;
            padding: 20px;
            border: 2px solid #333;
            font-size: 14px;
            line-height: 1.8;
            white-space: pre-wrap;
            margin-top: 16px;
        }}
        .url-info {{
            font-size: 12px;
            color: #666;
            margin-bottom: 32px;
            padding: 16px;
            background: #fff;
            border: 2px solid #333;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .url-info a {{
            color: #333;
            text-decoration: none;
            font-weight: bold;
        }}
        .url-info a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="url-info">SOURCE: <a href="{url}" target="_blank">{escaped_url_display}</a></div>
    <h1>CONTENT SUMMARY</h1>
"""]
        
        for section in sections:
            html_parts.append(f"""    <div class="section">
        <div class="section-title">{self._escape_html(section['title'])}</div>""")
            
            if 'summary' in section and section['summary']:
                html_parts.append(f"""        <div class="summary">
            <ul>""")
                for bullet in section['summary'].split('\n'):
                    if bullet.strip():
                        html_parts.append(f"                <li>{self._escape_html(bullet.lstrip('-•* ').strip())}</li>")
                html_parts.append("""            </ul>
        </div>""")
            
            html_parts.append(f"""        <div class="original-content">{self._escape_html(section['content'])}</div>
    </div>
""")
        
        html_parts.append("""</body>
</html>""")
        
        return '\n'.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _create_summary_view(self, html: str, url: str) -> str:
        """Create summary view from HTML content.
        
        Args:
            html: Original HTML content
            url: Source URL
            
        Returns:
            Summary HTML page
        """
        # Extract sections
        sections = self._extract_sections(html)
        
        if not sections:
            return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NO CONTENT FOUND</title>
    <style>
        body {{
            font-family: 'Courier New', Courier, monospace;
            padding: 32px;
            background: #fafafa;
            color: #333;
            line-height: 1.8;
        }}
        h1 {{
            font-size: 28px;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 3px solid #333;
            padding-bottom: 10px;
        }}
        p {{
            margin-bottom: 16px;
            font-size: 14px;
        }}
        a {{
            color: #333;
            text-decoration: none;
            font-weight: bold;
            border: 2px solid #333;
            padding: 8px 16px;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        a:hover {{
            background: #333;
            color: #fff;
        }}
    </style>
</head>
<body>
    <h1>NO CONTENT FOUND</h1>
    <p>COULD NOT EXTRACT MEANINGFUL CONTENT FROM THIS PAGE.</p>
    <p><a href="{url}">VIEW ORIGINAL PAGE</a></p>
</body>
</html>"""
        
        # Generate summaries for each section
        if self.window:
            self.window.evaluate_js("window.updateStatus('Generating summaries...')")
        
        for i, section in enumerate(sections):
            try:
                summary = self._generate_summary_bullets(section['title'], section['content'])
                section['summary'] = summary
                # Update progress
                progress = int((i + 1) / len(sections) * 100)
                if self.window:
                    self.window.evaluate_js(f"window.updateStatus('Generating summaries... {progress}%')")
            except Exception as e:
                logger.error(f"Error generating summary for section {i}: {e}")
                section['summary'] = ""
        
        # Create summary HTML
        return self._create_summary_html(sections, url)
    
    def _remove_media(self, html: str) -> str:
        """Remove all images and videos from HTML content.
        
        Args:
            html: HTML content
            
        Returns:
            HTML with images and videos removed, plus CSS/JS to prevent dynamic loading
        """
        # Remove <img> tags (including self-closing and with attributes)
        html = re.sub(r'<img[^>]*/?>', '', html, flags=re.IGNORECASE)
        
        # Remove <picture> elements and their contents
        html = re.sub(r'<picture[^>]*>.*?</picture>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove <video> elements (both with content and self-closing)
        html = re.sub(r'<video[^>]*>.*?</video>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<video[^>]*/?>', '', html, flags=re.IGNORECASE)
        
        # Remove <source> tags that are used for images or videos
        html = re.sub(r'<source[^>]*type=["\'](image|video)/[^"\']*["\'][^>]*>', '', html, flags=re.IGNORECASE)
        # Also remove source tags without explicit type if they're inside video/picture context
        # (we'll handle this more carefully - remove all source tags to be safe)
        html = re.sub(r'<source[^>]*/?>', '', html, flags=re.IGNORECASE)
        
        # Remove <iframe> tags (often used for embedded videos like YouTube, Vimeo)
        html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove <embed> tags (often used for videos)
        html = re.sub(r'<embed[^>]*/?>', '', html, flags=re.IGNORECASE)
        
        # Remove <object> tags (can contain videos)
        html = re.sub(r'<object[^>]*>.*?</object>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove <canvas> elements that might contain video frames
        html = re.sub(r'<canvas[^>]*>.*?</canvas>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<canvas[^>]*/?>', '', html, flags=re.IGNORECASE)
        
        # Remove background images from inline styles
        html = re.sub(r'background-image\s*:\s*[^;]*url\([^)]*\)[^;]*;?', '', html, flags=re.IGNORECASE)
        html = re.sub(r'background\s*:\s*[^;]*url\([^)]*\)[^;]*;?', '', html, flags=re.IGNORECASE)
        
        # Remove background-image from style attributes
        def remove_bg_from_style(match):
            style = match.group(1)
            # Remove background-image and background properties
            style = re.sub(r'background-image\s*:\s*[^;]*url\([^)]*\)[^;]*;?', '', style, flags=re.IGNORECASE)
            style = re.sub(r'background\s*:\s*[^;]*url\([^)]*\)[^;]*;?', '', style, flags=re.IGNORECASE)
            # Clean up multiple semicolons and trailing semicolons
            style = re.sub(r';+', ';', style).strip('; ')
            return f'style="{style}"' if style else ''
        
        html = re.sub(r'style="([^"]*)"', remove_bg_from_style, html, flags=re.IGNORECASE)
        
        # Inject CSS and JavaScript to prevent videos from playing and hide them
        # Find the head tag or create one, and inject CSS
        css_block = """
        <style id="epollo-media-blocker">
            video, img, picture, iframe[src*="youtube"], iframe[src*="vimeo"], 
            iframe[src*="dailymotion"], embed, object, canvas {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                width: 0 !important;
                height: 0 !important;
            }
        </style>
        """
        
        # Inject CSS into head or before </body>
        if '<head>' in html.lower():
            html = re.sub(r'(<head[^>]*>)', r'\1' + css_block, html, flags=re.IGNORECASE)
        elif '</head>' in html.lower():
            html = re.sub(r'(</head>)', css_block + r'\1', html, flags=re.IGNORECASE)
        else:
            # No head tag, add before body or at start
            if '<body' in html.lower():
                html = re.sub(r'(<body[^>]*>)', css_block + r'\1', html, flags=re.IGNORECASE)
            else:
                html = css_block + html
        
        # Inject JavaScript to remove dynamically added videos
        js_block = """
        <script>
        (function() {
            // Remove all video/img elements immediately
            function removeMedia() {
                document.querySelectorAll('video, img, picture, iframe, embed, object, canvas').forEach(function(el) {
                    el.remove();
                });
            }
            
            // Run immediately
            removeMedia();
            
            // Watch for dynamically added elements
            var observer = new MutationObserver(function(mutations) {
                removeMedia();
            });
            
            // Start observing when DOM is ready
            if (document.body) {
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            } else {
                document.addEventListener('DOMContentLoaded', function() {
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true
                    });
                });
            }
            
            // Prevent video playback
            document.addEventListener('play', function(e) {
                if (e.target.tagName === 'VIDEO' || e.target.tagName === 'AUDIO') {
                    e.preventDefault();
                    e.target.pause();
                    e.target.remove();
                }
            }, true);
        })();
        </script>
        """
        
        # Inject JavaScript before </body> or at end
        if '</body>' in html.lower():
            html = re.sub(r'(</body>)', js_block + r'\1', html, flags=re.IGNORECASE)
        else:
            html = html + js_block
        
        return html
    
    def _load_url(self, url: str, use_filter: bool = False):
        """Load URL and optionally filter content.
        
        Args:
            url: URL to load
            use_filter: Whether to apply content filtering
        """
        def load_thread():
            try:
                # Escape quotes for JavaScript
                def js_escape(text):
                    return text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')
                
                if self.window:
                    self.window.evaluate_js(f"window.updateStatus('Loading {url}...')")
                
                html, final_url = self._fetch_url(url)
                self.current_url = final_url
                
                # Check if summary view is enabled
                if self.config.summary_view:
                    # Create summary view instead of showing original page
                    if self.window:
                        self.window.evaluate_js("window.updateStatus('Creating summary view...')")
                    try:
                        html = self._create_summary_view(html, final_url)
                        if self.window:
                            self.window.evaluate_js("window.updateStatus('Summary view ready')")
                    except Exception as e:
                        logger.error(f"Error creating summary view: {e}", exc_info=True)
                        error_msg = str(e).replace('\\', '\\\\').replace("'", "\\'")
                        if self.window:
                            self.window.evaluate_js(f"window.updateStatus('Summary failed: {error_msg}')")
                        # Fall back to original page processing
                        if self.config.remove_images:
                            html = self._remove_media(html)
                else:
                    # Normal page processing
                    # Remove images and videos if configured
                    if self.config.remove_images:
                        html = self._remove_media(html)
                    
                    if use_filter and self.config.topics and self.content_filter:
                        if self.window:
                            self.window.evaluate_js("window.updateStatus('Filtering content...')")
                        try:
                            html = self.content_filter.filter_content(html, self.config.topics)
                            if self.window:
                                self.window.evaluate_js("window.updateStatus('Content filtered')")
                        except RuntimeError as e:
                            # Filtering failed, but continue with original content
                            error_msg = str(e).replace('\\', '\\\\').replace("'", "\\'")
                            if self.window:
                                self.window.evaluate_js(f"window.updateStatus('Filtering failed: {error_msg}')")
                            # Continue with unfiltered HTML
                    else:
                        if self.window:
                            self.window.evaluate_js("window.updateStatus('Loaded')")
                
                # Store HTML and update frame
                self._html_content = html
                
                # Update URL bar and load content only if window exists
                if self.window:
                    escaped_url = js_escape(final_url)
                    self.window.evaluate_js(f"window.updateUrl('{escaped_url}')")
                    
                    # Load content into iframe using base64 data URI (safer for special characters)
                    import base64
                    encoded_html = base64.b64encode(html.encode('utf-8')).decode('utf-8')
                    data_uri = f"data:text/html;charset=utf-8;base64,{encoded_html}"
                    self.window.evaluate_js(f"""
                        const frame = document.getElementById('content-frame');
                        frame.src = '{data_uri}';
                    """)
                
            except Exception as e:
                logger.error(f"Error loading URL: {e}", exc_info=True)
                # Show error in status, but the error HTML was already returned by _fetch_url
                error_msg = str(e).replace('\\', '\\\\').replace("'", "\\'")[:100]  # Limit length
                if self.window:
                    self.window.evaluate_js(f"window.updateStatus('Error: {error_msg}')")
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def navigate(self, url: str, use_filter: bool = False):
        """Navigate to URL.
        
        Args:
            url: URL to navigate to
            use_filter: Whether to apply content filtering
        """
        self._load_url(url, use_filter)
    
    def take_screenshot(
        self,
        output_path: Optional[str] = None,
        width: int = 1200,
        height: int = 800,
        full_page: bool = True,
        quality: int = 90,
        format: str = 'png'
    ) -> bytes:
        """Take a screenshot of the current page or HTML content.
        
        Args:
            output_path: Optional path to save screenshot
            width: Image width
            height: Image height
            full_page: Whether to capture full page
            quality: Image quality (1-100) for JPEG
            format: Image format ('png', 'jpeg', 'webp')
            
        Returns:
            Screenshot as bytes
        """
        if not self._html_content:
            raise ValueError("No HTML content loaded. Navigate to a URL first.")
        
        try:
            return render_html_to_screenshot_sync(
                html=self._html_content,
                output_path=output_path,
                width=width,
                height=height,
                full_page=full_page,
                quality=quality,
                format=format
            )
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            raise
    
    def take_url_screenshot(
        self,
        url: str,
        output_path: Optional[str] = None,
        width: int = 1200,
        height: int = 800,
        full_page: bool = True,
        quality: int = 90,
        format: str = 'png',
        use_filter: bool = False
    ) -> bytes:
        """Take a screenshot of a URL directly.
        
        Args:
            url: URL to screenshot
            output_path: Optional path to save screenshot
            width: Image width
            height: Image height
            full_page: Whether to capture full page
            quality: Image quality (1-100) for JPEG
            format: Image format ('png', 'jpeg', 'webp')
            use_filter: Whether to apply content filtering
            
        Returns:
            Screenshot as bytes
        """
        try:
            # If filtering is enabled, fetch and filter the HTML first
            if use_filter and self.config.topics and self.content_filter:
                html, _ = self._fetch_url(url)
                html = self.content_filter.filter_content(html, self.config.topics)
                
                return render_html_to_screenshot_sync(
                    html=html,
                    output_path=output_path,
                    width=width,
                    height=height,
                    full_page=full_page,
                    quality=quality,
                    format=format
                )
            else:
                # Render URL directly
                return render_url_to_screenshot_sync(
                    url=url,
                    output_path=output_path,
                    width=width,
                    height=height,
                    full_page=full_page,
                    quality=quality,
                    format=format
                )
        except Exception as e:
            logger.error(f"Error taking URL screenshot: {e}")
            raise
    
    def create_window(self):
        """Create and show browser window."""
        html = self._create_html_ui()
        
        # Create API instance to avoid serializing the entire Browser object
        api = BrowserAPI(self)
        
        self.window = webview.create_window(
            'Epollo Browser',
            html=html,
            width=1200,
            height=800,
            min_size=(800, 600),
            js_api=api
        )
        
        webview.start(debug=False)


def take_url_screenshot(
    url: str,
    output_path: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
    full_page: bool = True,
    quality: int = 90,
    format: str = 'png',
    use_filter: bool = False,
    config: Optional[Config] = None,
    fallback: bool = True
) -> bytes:
    """Take a screenshot of a URL without requiring a Browser instance.
    
    This is a convenience function that creates minimal browser state
    for taking screenshots without initializing the full browser UI.
    
    Args:
        url: URL to screenshot
        output_path: Optional path to save screenshot
        width: Image width
        height: Image height
        full_page: Whether to capture full page
        quality: Image quality (1-100) for JPEG
        format: Image format ('png', 'jpeg', 'webp')
        use_filter: Whether to apply content filtering
        config: Optional configuration instance
        fallback: Whether to try fallback methods for paywalled sites
        
    Returns:
        Screenshot as bytes
    """
    try:
        # If filtering is enabled, create Browser instance with content filter
        if use_filter and (config and config.topics):
            browser = Browser(config)
            return browser.take_url_screenshot(
                url=url,
                output_path=output_path,
                width=width,
                height=height,
                full_page=full_page,
                quality=quality,
                format=format,
                use_filter=use_filter
            )
        else:
            # Try direct rendering first
            try:
                return render_url_to_screenshot_sync(
                    url=url,
                    output_path=output_path,
                    width=width,
                    height=height,
                    full_page=full_page,
                    quality=quality,
                    format=format
                )
            except Exception as direct_error:
                logger.warning(f"Direct rendering failed, trying fetch-and-render approach: {direct_error}")
                
                # Fallback: fetch HTML and render it (bypasses some paywalls)
                import requests
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
                response.raise_for_status()
                
                # Check if we got an access denied page
                if 'access denied' in response.text.lower() or '403' in response.text:
                    if fallback:
                        logger.warning("Got access denied page, trying cached version")
                        # Try cached version
                        try:
                            cache_url = f"https://webcache.googleusercontent.com/search?q={url}"
                            cache_response = requests.get(cache_url, headers=headers, timeout=30, allow_redirects=True)
                            if cache_response.status_code == 200:
                                return render_html_to_screenshot_sync(
                                    html=cache_response.text,
                                    output_path=output_path,
                                    width=width,
                                    height=height,
                                    full_page=full_page,
                                    quality=quality,
                                    format=format
                                )
                        except Exception as cache_error:
                            logger.warning(f"Cache fallback failed: {cache_error}")
                    
                    # Try with different user agent or add referer
                    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    headers['Referer'] = 'https://www.google.com/'
                    response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
                
                return render_html_to_screenshot_sync(
                    html=response.text,
                    output_path=output_path,
                    width=width,
                    height=height,
                    full_page=full_page,
                    quality=quality,
                    format=format
                )
    
    except Exception as e:
        logger.error(f"Error taking URL screenshot: {e}")
        raise

