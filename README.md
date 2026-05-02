# Epollo

A person-centric browser with AI-based content filtering.

Epollo lets you browse the web while automatically removing content related to user-configurable topics using OpenAI APIs.

## Features

- Minimal browser UI (URL bar + filter toggle)
- Topic-based HTML filtering with OpenAI
- Screenshot capture utilities
- Optional OCR and vision extraction helpers

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your API key:

```bash
export OPENAI_API_KEY=your_key_here
```

3. Configure `config.yaml`:

```yaml
topics:
  - "advertising"

openai:
  model: "gpt-4.1-mini"

filtering:
  enabled: true
```

4. Run:

```bash
python run.py
```

## License

MIT
