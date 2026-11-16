# Automated Multi-Platform Posting System

A FastAPI-based REST API service that receives a short message, validates it, and publishes it across multiple third-party platforms through their official APIs.

## Project Structure

```text
dxora_python_practical_test/
│
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── config.py
│   │
│   ├── platforms/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── bluesky.py
│   │   ├── telegram.py
│   │   ├── mastodon.py
│   │   ├── devto.py
│   │   └── discord.py
│   │
│   └── services/
│       ├── __init__.py
│       └── posting_service.py
│
├── tests/
│   ├── test_posting.py
│   └── test_api.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Supported Platforms (5 Platforms)

1. **Bluesky** (via AT Protocol XRPC)
2. **Telegram** (via Telegram Bot API)
3. **Mastodon** (via Mastodon REST API)
4. **DEV.to** (via DEV.to Articles API)
5. **Discord** (via Discord Incoming Webhooks)

## Setup & Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

4. Run the development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 4000
   ```

5. Access Swagger documentation:
   Open [http://localhost:4000/docs](http://localhost:4000/docs) in your browser.

## API Endpoints

### `POST /posting`
Publish a short marketing or announcement message across all configured platforms.

**Validation Rules:**
- **Length:** Maximum 200 characters.
- **CTA Link:** Must contain exactly one CTA URL.
- **Allowed Schemes:** `http` and `https` only.
- **Host Validation:** URL must contain a structurally valid hostname (domain, localhost, or IPv4).
- **Rejection:** Empty messages, missing URLs, multiple URLs, malformed URLs, and unsupported schemes return `422 Unprocessable Entity` and never execute platform posting.
