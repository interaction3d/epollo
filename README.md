# Epollo

![logo](./logo.png)

A person-centric browser with LLM-based content filtering. Epollo allows you to browse the web however you want, while automatically removing content related to user-configurable topics using a local LLM (via Ollama).

## Features

- **Minimalistic UI**: Clean, simple interface with URL bar and filter toggle
- **User defined configuration**: A person-centric way to config your browser experience
- **Web Rendering**: Full JavaScript support using system browser engine (via pywebview)
- **Content Filtering**: Remove content related to configurable topics using local LLM


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


### Using the Browser

## How It Works

1. User enters a list of URLs
2. Browser fetches the HTML content from the URL at a given time in the day
3. If filtering is enabled:
   - HTML is sent to Ollama with a prompt to remove topic-related content
   - Ollama processes the HTML and returns filtered version
   - Filtered HTML is rendered in the browser
4. If filtering is disabled, original HTML is rendered directly
5. Generate a webpage containing the daily digest.


## License
MIT