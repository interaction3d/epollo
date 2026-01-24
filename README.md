# Epollo

![logo](./logo.png)

A lightweight Python browser with LLM-based content filtering. Epollo allows you to browse the web while automatically removing content related to user-configurable topics using a local LLM (via Ollama).

## Features

- **Minimalistic UI**: Clean, simple interface with URL bar and filter toggle
- **Web Rendering**: Full JavaScript support using system browser engine (via pywebview)
- **Content Filtering**: Remove content related to configurable topics using local LLM
- **Screenshot Functionality**: Capture screenshots of web pages and HTML content
- **Real-time URL Changes**: Navigate to any URL at any time
- **Lightweight**: Minimal dependencies, fast startup

## Requirements

- Python 3.9 or higher
- [Ollama](https://ollama.ai/) installed and running (for content filtering)
- An Ollama model (e.g., `llama3.2`) downloaded
- Playwright browsers (for screenshot functionality)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd epollo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers (for screenshot functionality):
```bash
python -m playwright install chromium
```

4. Install and start Ollama:
   - Download from https://ollama.ai/
   - Start Ollama service
   - Pull a model: `ollama pull llama3.2`

## Running Ollama Locally

### Start the Ollama Server

Before running Epollo, you need to start the Ollama server:

```bash
# Start Ollama server (keep this terminal open)
ollama serve
```

**Note:** On macOS, Ollama may run automatically as a background service after installation. If `ollama serve` says the port is already in use, Ollama is likely already running.

### Download a Model

Download a model for local use (recommended small models for faster performance):

```bash
# Small, fast models (good for MacBook Pro)
ollama pull qwen2.5:1.5b     # ~1.6GB - fastest
ollama pull llama3.2:1b      # ~1.3GB - very fast
ollama pull phi3:mini        # ~2.3GB - good balance

# List downloaded models
ollama list
```

### Test Locally

Test that Ollama is working correctly:

```bash
# Test Ollama connection - runs a simple test script that sends a chat message to verify Ollama is working
python epollo/models/run.py
```

Or test the model directly:

```bash
# Test a model
ollama run qwen2.5:1.5b "Hello, how are you?"
```

### Verify Ollama is Running

Check if Ollama is accessible:

```bash
# Check Ollama API
curl http://localhost:11434/api/tags

# Or test with Python
python3 -c "import ollama; print(ollama.list())"
```

## Configuration

Edit `config.yaml` to customize filtering topics and Ollama settings:

```yaml
topics:
  - "advertising"
  - "sponsored content"
  - "newsletter signup"

ollama:
  model: "llama3.2"  # Ollama model name
  api_url: "http://localhost:11434"  # Ollama API URL

filtering:
  enabled: true  # Default filter state
```

## Usage

Run the browser:
```bash
python -m epollo.main
```

Or:
```bash
python epollo/main.py
```

### Using the Browser

1. **Enter a URL**: Type a URL in the address bar and press Enter
2. **Toggle Filtering**: Click the "Filter" button to enable/disable content filtering
3. **Take Screenshots**: Click the "Screenshot" button to capture the current page
4. **Navigate**: Change the URL at any time to browse different websites

When filtering is enabled, the browser will:
- Fetch the webpage HTML
- Send it to Ollama with instructions to remove content related to configured topics
- Display the filtered content while maintaining document flow

#### Screenshot Functionality

The browser includes built-in screenshot capabilities:

- **Click Screenshot Button**: Capture current page with one click
- **Automatic Saving**: Screenshots are saved to the `screenshots/` directory with timestamp
- **High Quality**: Full-page capture with customizable dimensions
- **Multiple Formats**: Support for PNG, JPEG, and WebP formats

**Programmatic Screenshot Usage:**

```python
from epollo.browser import Browser

# Create browser instance
browser = Browser()

# Screenshot from URL
screenshot_bytes = browser.take_url_screenshot(
    url="https://example.com",
    output_path="screenshot.png",
    width=1200,
    height=800,
    full_page=True
)

# Screenshot after navigation
browser.navigate("https://example.com")
screenshot_bytes = browser.take_screenshot(
    output_path="nav_screenshot.png",
    width=1200,
    height=800
)
```

**Standalone Screenshot Functions:**

```python
from epollo.screenshot import render_html_to_screenshot_sync, render_url_to_screenshot_sync

# HTML to screenshot
html_content = "<html><body><h1>Hello World</h1></body></html>"
screenshot_bytes = render_html_to_screenshot_sync(
    html=html_content,
    output_path="html_screenshot.png",
    width=1200,
    height=800
)

# URL to screenshot
screenshot_bytes = render_url_to_screenshot_sync(
    url="https://example.com",
    output_path="url_screenshot.png",
    width=1200,
    height=800,
    full_page=True
)
```

## How It Works

1. User enters a URL in the address bar
2. Browser fetches the HTML content from the URL
3. If filtering is enabled:
   - HTML is sent to Ollama with a prompt to remove topic-related content
   - Ollama processes the HTML and returns filtered version
   - Filtered HTML is rendered in the browser
4. If filtering is disabled, original HTML is rendered directly

## Error Handling

The browser handles various error scenarios gracefully:
- **Network errors**: Displays user-friendly error messages
- **Invalid URLs**: Validates and reports URL format errors
- **Ollama connection issues**: Falls back to unfiltered content with warnings
- **Timeout errors**: Handles slow connections with appropriate messages

## Project Structure

```
epollo/
├── epollo/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── browser.py           # Main browser window with screenshot support
│   ├── content_filter.py    # Ollama integration
│   ├── screenshot.py        # Screenshot functionality using Playwright
│   └── config.py            # Configuration management
├── requirements.txt
├── config.yaml              # User configuration
└── README.md
```

## Notes

- Content filtering requires Ollama to be running
- Large pages (>10MB) are not supported
- Filtering may take some time depending on page size and Ollama model speed
- The browser uses an iframe to render content, which may have some limitations with certain websites
- Screenshot functionality requires Playwright browsers to be installed (`python -m playwright install chromium`)
- Screenshots are automatically saved to the `screenshots/` directory with timestamp filenames
- For batch screenshot operations, consider using the async API for better performance

## License

[Add your license here]
