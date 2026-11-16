# Automated Multi-Platform Posting System

A Python API that allows users to publish one message to multiple social media platforms through a single request.

This project was developed as part of a Python practical assignment. It uses FastAPI and the official APIs of the supported platforms.

## Features

- Publish one message to five different platforms.
- Validate messages before publishing.
- Allow only HTTP and HTTPS URLs.
- Require exactly one CTA URL per message.
- Limit messages to 200 characters.
- Handle each platform independently, so one failure does not stop the others.
- Return a result for each platform, including its status, post URL, date, time, and error if something goes wrong.

## Supported Platforms

1. Bluesky
2. Telegram
3. Mastodon
4. DEV.to
5. Discord

Each platform uses its own API integration and credentials.

## Technologies Used

- Python 3
- FastAPI
- Pydantic
- HTTPX
- Uvicorn
- Pytest

## Project Structure

```text
project/
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
│       └── posting_service.py
│
├── tests/
│   ├── test_api.py
│   └── test_posting.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/DE-TeAcH/dxora-python-practical-test
cd dxora-python-practical-test
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

An `.env.example` file is included in the project with the required environment variable names.

Create your own `.env` file by copying `.env.example`:

**Windows:**
```bash
copy .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

Open the `.env` file and add your own API credentials for each platform you want to use.

**Important:** Keep your `.env` file private. Never upload your API tokens or credentials to GitHub.

## Running the API

Start the server with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

The API will be available at:

```text
http://localhost:4000
```

You can access the interactive API documentation through Swagger:

```text
http://localhost:4000/docs
```

## API Usage

### POST /posting

This endpoint publishes a message to all configured platforms.

**Request body:**

```json
{
    "message": "Check out developer's portfolio: https://zouatinezakaria.vercel.app"
}
```

### Validation Rules

Before publishing, the API checks that:

- The message is not empty.
- The message does not exceed 200 characters.
- It contains exactly one URL.
- The URL uses HTTP or HTTPS.
- The URL contains a valid hostname.

Invalid requests return HTTP `422` and are rejected before any platform publishing operation starts.

### Example Response for both failure and success

```json
{
    "success": true,
    "results": [
        {
            "platform": "Bluesky",
            "status": "success",
            "posted_url": "https://bsky.app/profile/zouatinedezaki.bsky.social/post/3n2hl62qgsn2u",
            "public_access": true,
            "date": "2026-11-16",
            "time": "22:27:22",
            "error": null
        },
        {
            "platform": "Telegram",
            "status": "success",
            "posted_url": "https://t.me/Dxora_publisher_ByZak/8",
            "public_access": true,
            "date": "2026-11-16",
            "time": "22:27:22",
            "error": null
        },
        {
            "platform": "Mastodon",
            "status": "success",
            "posted_url": "https://mastodon.social/@de_zak/117628472064575348",
            "public_access": true,
            "date": "2026-11-16",
            "time": "22:27:22",
            "error": null
        },
        {
            "platform": "DEV.to",
            "status": "success",
            "posted_url": "https://dev.to/zouatine_zakaria/check-my-portfolio-mi0",
            "public_access": true,
            "date": "2026-11-16",
            "time": "22:27:23",
            "error": null
        },
        {
            "platform": "Discord",
            "status": "success",
            "posted_url": null,
            "public_access": false,
            "date": "2026-11-16",
            "time": "22:27:24",
            "error": null
        }
    ]
}
{
    "success": true,
    "results": [
        {
            "platform": "Bluesky",
            "status": "success",
            "posted_url": "https://bsky.app/profile/zouatinedezaki.bsky.social/post/3n2hl62qgsn2u",
            "public_access": true,
            "date": "2026-11-16",
            "time": "22:27:22",
            "error": null
        },
        {
            "platform": "Telegram",
            "status": "failed",
            "posted_url": null,
            "public_access": false,
            "date": null,
            "time": null,
            "error": "Telegram API error (HTTP 400): Bad Request: chat not found"
        },
        {
            "platform": "Mastodon",
            "status": "success",
            "posted_url": "https://mastodon.social/@de_zak/117628472064575348",
            "public_access": true,
            "date": "2026-11-16",
            "time": "22:27:22",
            "error": null
        },
        {
            "platform": "DEV.to",
            "status": "failed",
            "posted_url": null,
            "public_access": false,
            "date": null,
            "time": null,
            "error": "DEV.to credentials not configured (DEVTO_API_KEY missing)"
        },
        {
            "platform": "Discord",
            "status": "success",
            "posted_url": null,
            "public_access": false,
            "date": "2026-11-16",
            "time": "22:27:24",
            "error": null
        }
    ]
}
{
    "success": false,
    "results": [
        {
            "platform": "Bluesky",
            "status": "failed",
            "posted_url": null,
            "public_access": false,
            "date": null,
            "time": null,
            "error": "Bluesky credentials not configured (BSKY_HANDLE or BSKY_APP_PASSWORD missing)"
        },
        {
            "platform": "Telegram",
            "status": "failed",
            "posted_url": null,
            "public_access": false,
            "date": null,
            "time": null,
            "error": "Telegram credentials not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)"
        },
        {
            "platform": "Mastodon",
            "status": "failed",
            "posted_url": null,
            "public_access": false,
            "date": null,
            "time": null,
            "error": "Mastodon credentials not configured (MASTODON_INSTANCE_URL or MASTODON_ACCESS_TOKEN missing)"
        },
        {
            "platform": "DEV.to",
            "status": "failed",
            "posted_url": null,
            "public_access": false,
            "date": null,
            "time": null,
            "error": "DEV.to credentials not configured (DEVTO_API_KEY missing)"
        },
        {
            "platform": "Discord",
            "status": "failed",
            "posted_url": null,
            "public_access": false,
            "date": null,
            "time": null,
            "error": "Discord credentials not configured (DISCORD_WEBHOOK_URL missing)"
        }
    ]
}
```

The example above is shortened for readability.

The `success` field is `true` when at least one platform publishes successfully. It is `false` only when all platforms fail.

Some platforms may not provide a publicly accessible post URL. In that case, `posted_url` is `null` and `public_access` is `false`.

## Running Tests

Run the test suite using:

```bash
pytest
```

The tests cover message validation, platform responses, API errors, missing credentials, and failure handling.

## Notes

- Platform credentials must be configured before publishing.
- Each platform handles its own publishing errors.
- Automated tests use mocked API responses, so they do not publish real posts.
- Real publishing requires valid platform credentials and the necessary permissions.
- DEV.to publishes content as an article rather than a standard short social media post.
- Discord uses an incoming webhook to publish messages to a configured channel.

## Author

Developed as part of a Python practical assignment.