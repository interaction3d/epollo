# Epollo

[logo](./logo.png)

A lightweight Python browser with LLM-based content filtering. Epollo allows you to browse the web while automatically removing content related to user-configurable topics using a local LLM (via Ollama).

## Features

- **Minimalistic UI**: Clean, simple interface with URL bar and filter toggle
- **Web Rendering**: Full JavaScript support using system browser engine (via pywebview)
- **Content Filtering**: Remove content related to configurable topics using local LLM
- **Real-time URL Changes**: Navigate to any URL at any time
- **Lightweight**: Minimal dependencies, fast startup

## Requirements

- Python 3.9 or higher
- [Ollama](https://ollama.ai/) installed and running (for content filtering)
- An Ollama model (e.g., `llama3.2`) downloaded

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

3. Install and start Ollama:
   - Download from https://ollama.ai/
   - Start Ollama service
   - Pull a model: `ollama pull llama3.2`

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
3. **Navigate**: Change the URL at any time to browse different websites

When filtering is enabled, the browser will:
- Fetch the webpage HTML
- Send it to Ollama with instructions to remove content related to configured topics
- Display the filtered content while maintaining document flow

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
│   ├── browser.py           # Main browser window
│   ├── content_filter.py    # Ollama integration
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

## License

[Add your license here]
