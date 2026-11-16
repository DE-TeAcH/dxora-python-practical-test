from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.telegram import TelegramPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.devto import DevtoPlatform
from app.platforms.discord import DiscordPlatform
from app.schemas import PlatformPostResult
from app.services.posting_service import PostingService

client = TestClient(app)


# ---------------------------------------------------------
# Scenario 1: Foundation Tests (Phase 1)
# ---------------------------------------------------------

def test_root():
    """Verify root endpoint works."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Automated Multi-Platform Posting System is running"


def test_health():
    """Verify health endpoint works."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ---------------------------------------------------------
# Scenario 2: Validation Tests (Phase 3 & 5 Requirements)
# ---------------------------------------------------------

def test_validation_199_characters():
    """Valid message of exactly 199 characters."""
    url = " https://example.com"
    msg = "A" * (199 - len(url)) + url
    assert len(msg) == 199

    with patch.object(
        PostingService, "post_to_all", return_value={"success": True, "results": []}
    ):
        response = client.post("/posting", json={"message": msg})
        assert response.status_code == 200


def test_validation_200_characters():
    """Valid message of exactly 200 characters."""
    url = " https://example.com"
    msg = "A" * (200 - len(url)) + url
    assert len(msg) == 200

    with patch.object(
        PostingService, "post_to_all", return_value={"success": True, "results": []}
    ):
        response = client.post("/posting", json={"message": msg})
        assert response.status_code == 200


def test_validation_201_characters_rejected():
    """Reject message exceeding 200 characters."""
    url = " https://example.com"
    msg = "A" * (201 - len(url)) + url
    assert len(msg) == 201
    response = client.post("/posting", json={"message": msg})
    assert response.status_code == 422
    assert "exceeds 200 characters" in response.text


def test_validation_empty_message_rejected():
    """Reject empty message."""
    response = client.post("/posting", json={"message": ""})
    assert response.status_code == 422
    assert "cannot be empty" in response.text


def test_validation_whitespace_only_message_rejected():
    """Reject whitespace-only message."""
    response = client.post("/posting", json={"message": "    \n\t  "})
    assert response.status_code == 422
    assert "cannot be empty" in response.text


def test_validation_zero_urls_rejected():
    """Reject message containing zero URLs."""
    response = client.post("/posting", json={"message": "Check out our new business platform."})
    assert response.status_code == 422
    assert "exactly one CTA URL (found 0)" in response.text


def test_validation_multiple_urls_rejected():
    """Reject message containing more than one URL."""
    payload = {
        "message": "Visit https://example.com and check https://dxora.com"
    }
    response = client.post("/posting", json=payload)
    assert response.status_code == 422
    assert "exactly one CTA URL (found 2)" in response.text


def test_validation_unsupported_scheme_ftp_rejected():
    """Reject message with an unsupported URL scheme."""
    payload = {
        "message": "Download from: ftp://files.example.com"
    }
    response = client.post("/posting", json=payload)
    assert response.status_code == 422
    assert "Unsupported URL scheme" in response.text


def test_validation_malformed_url_no_host_rejected():
    """Reject message with a malformed URL missing network location/host."""
    response = client.post("/posting", json={"message": "Check out http://"})
    assert response.status_code == 422
    assert "Malformed URL" in response.text


def test_validation_malformed_url_slash_only_rejected():
    """Reject message with a malformed URL (http:///)."""
    response = client.post("/posting", json={"message": "Check out http:///"})
    assert response.status_code == 422
    assert "Malformed URL" in response.text


def test_validation_invalid_hostname_rejected():
    """Reject message containing an invalid hostname."""
    response = client.post("/posting", json={"message": "Check out http://invalid_host_name"})
    assert response.status_code == 422
    assert "Invalid URL hostname" in response.text


def test_validation_invalid_request_never_triggers_platforms():
    """Verify that an invalid request does not trigger any platform posting handlers."""
    with patch("app.services.posting_service.PostingService.post_to_all") as mock_post_all:
        response = client.post("/posting", json={"message": "Invalid message with no URL"})
        assert response.status_code == 422
        mock_post_all.assert_not_called()


# ---------------------------------------------------------
# Scenario 3: End-to-End Workflow & Response Structure (5 Platforms)
# ---------------------------------------------------------

def test_posting_workflow_all_success_and_response_structure():
    """Verify POST /posting returns results matching the exact required response contract for all 5 platforms."""
    payload = {
        "message": "Check out our latest business platform. https://example.com"
    }
    with patch.object(
        BlueskyPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="Bluesky",
            status="success",
            posted_url="https://bsky.app/profile/test.bsky.social/post/3lb123",
            public_access=True,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ), patch.object(
        TelegramPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="Telegram",
            status="success",
            posted_url="https://t.me/test_channel/42",
            public_access=True,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ), patch.object(
        MastodonPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="Mastodon",
            status="success",
            posted_url="https://mastodon.social/@test/123",
            public_access=True,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ), patch.object(
        DevtoPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="DEV.to",
            status="success",
            posted_url="https://dev.to/test/article-123",
            public_access=True,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ), patch.object(
        DiscordPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="Discord",
            status="success",
            posted_url=None,
            public_access=False,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ):
        response = client.post("/posting", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 5

        expected_platforms = ["Bluesky", "Telegram", "Mastodon", "DEV.to", "Discord"]
        actual_platforms = [r["platform"] for r in data["results"]]
        assert actual_platforms == expected_platforms

        # Verify all 7 required schema fields in every result
        for result in data["results"]:
            assert "platform" in result
            assert "status" in result
            assert "posted_url" in result
            assert "public_access" in result
            assert "date" in result
            assert "time" in result
            assert "error" in result
            assert result["status"] == "success"
            assert result["error"] is None


def test_posting_partial_failure():
    """Verify one platform failure does not stop other platforms (error isolation across 5 platforms)."""
    payload = {
        "message": "Check out our latest business platform. https://example.com"
    }
    with patch.object(
        BlueskyPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="Bluesky",
            status="success",
            posted_url="https://bsky.app/profile/test/post/123",
            public_access=True,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ), patch.object(
        TelegramPlatform,
        "post",
        side_effect=RuntimeError("Simulated Telegram connection failure"),
    ), patch.object(
        MastodonPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="Mastodon",
            status="success",
            posted_url="https://mastodon.social/@test/123",
            public_access=True,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ), patch.object(
        DevtoPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="DEV.to",
            status="success",
            posted_url="https://dev.to/test/article-123",
            public_access=True,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ), patch.object(
        DiscordPlatform,
        "post",
        return_value=PlatformPostResult(
            platform="Discord",
            status="success",
            posted_url=None,
            public_access=False,
            date="2026-11-16",
            time="12:00:00",
            error=None,
        ),
    ):
        response = client.post("/posting", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True  # Overall success is True because others succeeded
        assert len(data["results"]) == 5

        results_by_platform = {r["platform"]: r for r in data["results"]}

        # Telegram should have failed with error recorded
        assert results_by_platform["Telegram"]["status"] == "failed"
        assert "Simulated Telegram connection failure" in results_by_platform["Telegram"]["error"]
        assert results_by_platform["Telegram"]["posted_url"] is None

        # Bluesky, Mastodon, DEV.to, and Discord must have succeeded
        assert results_by_platform["Bluesky"]["status"] == "success"
        assert results_by_platform["Mastodon"]["status"] == "success"
        assert results_by_platform["DEV.to"]["status"] == "success"
        assert results_by_platform["Discord"]["status"] == "success"


def test_posting_all_platforms_fail():
    """Verify top-level success is False when all 5 platforms fail."""
    payload = {
        "message": "Check out our latest business platform. https://example.com"
    }
    with patch.object(
        BlueskyPlatform, "post", side_effect=RuntimeError("Bluesky down")
    ), patch.object(
        TelegramPlatform, "post", side_effect=RuntimeError("Telegram down")
    ), patch.object(
        MastodonPlatform, "post", side_effect=RuntimeError("Mastodon down")
    ), patch.object(
        DevtoPlatform, "post", side_effect=RuntimeError("DEV.to down")
    ), patch.object(
        DiscordPlatform, "post", side_effect=RuntimeError("Discord down")
    ):
        response = client.post("/posting", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert len(data["results"]) == 5
        for r in data["results"]:
            assert r["status"] == "failed"


# ---------------------------------------------------------
# Scenario 4: Missing Credentials & Error Isolation (No Crash)
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_all_platforms_missing_credentials():
    """Verify all 5 platforms handle unconfigured credentials without crashing."""
    service = PostingService(platforms=[
        BlueskyPlatform(handle="", app_password=""),
        TelegramPlatform(bot_token="", chat_id=""),
        MastodonPlatform(instance_url="", access_token=""),
        DevtoPlatform(api_key=""),
        DiscordPlatform(webhook_url=""),
    ])
    response = await service.post_to_all("Test message https://example.com")
    assert response.success is False
    assert len(response.results) == 5
    for r in response.results:
        assert r.status == "failed"
        assert "credentials not configured" in r.error


# ---------------------------------------------------------
# Scenario 5: Bluesky Unit Tests (Mocked)
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_bluesky_successful_publishing():
    """Verify Bluesky session creation, record publishing, and genuine public URL extraction."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "com.atproto.server.createSession" in url_str:
            return httpx.Response(
                200,
                json={
                    "accessJwt": "mock-access-jwt-token",
                    "did": "did:plc:mockdid12345",
                    "handle": "dxora.bsky.social"
                }
            )
        elif "com.atproto.repo.createRecord" in url_str:
            return httpx.Response(
                200,
                json={
                    "uri": "at://did:plc:mockdid12345/app.bsky.feed.post/3lbrecordkey789",
                    "cid": "bafyreimockcid12345"
                }
            )
        return httpx.Response(404)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = BlueskyPlatform(
        handle="dxora.bsky.social",
        app_password="test-app-password",
        service_url="https://bsky.social",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Bluesky"
    assert result.status == "success"
    assert result.posted_url == "https://bsky.app/profile/dxora.bsky.social/post/3lbrecordkey789"
    assert result.public_access is True
    assert result.date is not None
    assert result.time is not None
    assert result.error is None


@pytest.mark.anyio
async def test_bluesky_auth_failure():
    """Verify Bluesky handles 401 authentication errors safely without exposing secrets."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Authentication Required"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = BlueskyPlatform(
        handle="dxora.bsky.social",
        app_password="bad-password",
        service_url="https://bsky.social",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Bluesky"
    assert result.status == "failed"
    assert "Bluesky auth error (HTTP 401)" in result.error
    assert "bad-password" not in result.error


@pytest.mark.anyio
async def test_bluesky_timeout():
    """Verify Bluesky handles network timeouts gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = BlueskyPlatform(
        handle="dxora.bsky.social",
        app_password="test-password",
        service_url="https://bsky.social",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Bluesky"
    assert result.status == "failed"
    assert result.error == "Bluesky request timed out"


# ---------------------------------------------------------
# Scenario 6: Telegram Unit Tests (Mocked)
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_telegram_successful_public_channel():
    """Verify Telegram publishing to a public channel returns genuine public link and public_access=True."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 42,
                    "date": 1773783068,
                    "chat": {
                        "id": -100123456789,
                        "title": "Dxora News",
                        "username": "dxora_news",
                        "type": "channel"
                    },
                    "text": "Check out our launch! https://example.com"
                }
            }
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = TelegramPlatform(
        bot_token="123456:FAKE_TOKEN_ABC",
        chat_id="@dxora_news",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Telegram"
    assert result.status == "success"
    assert result.posted_url == "https://t.me/dxora_news/42"
    assert result.public_access is True
    assert result.date is not None
    assert result.time is not None
    assert result.error is None


@pytest.mark.anyio
async def test_telegram_private_channel_or_chat():
    """Verify Telegram publishing to a private channel/chat returns public_access=False and posted_url=None."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 99,
                    "date": 1773783068,
                    "chat": {
                        "id": -100987654321,
                        "title": "Private Team Group",
                        "type": "supergroup"
                    },
                    "text": "Internal announcement https://example.com"
                }
            }
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = TelegramPlatform(
        bot_token="123456:FAKE_TOKEN_ABC",
        chat_id="-100987654321",
        client=mock_client
    )

    result = await platform.post("Internal announcement https://example.com")

    assert result.platform == "Telegram"
    assert result.status == "success"
    assert result.posted_url is None
    assert result.public_access is False


@pytest.mark.anyio
async def test_telegram_token_redaction_in_errors():
    """Verify that Telegram bot tokens in request URLs or exception strings are strictly redacted."""
    sensitive_token = "SECRET_BOT_TOKEN_123456789"

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.RequestError(f"Failed to connect to https://api.telegram.org/bot{sensitive_token}/sendMessage")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = TelegramPlatform(
        bot_token=sensitive_token,
        chat_id="@dxora_news",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Telegram"
    assert result.status == "failed"
    assert sensitive_token not in result.error
    assert "[REDACTED]" in result.error


@pytest.mark.anyio
async def test_telegram_timeout():
    """Verify Telegram handles network timeouts gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = TelegramPlatform(
        bot_token="123456:FAKE_TOKEN_ABC",
        chat_id="@dxora_news",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Telegram"
    assert result.status == "failed"
    assert result.error == "Telegram request timed out"


# ---------------------------------------------------------
# Scenario 7: Mastodon Unit Tests (Mocked)
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_mastodon_successful_publishing():
    """Verify Mastodon publishes with public visibility and extracts response url and timestamp."""
    request_captured = {}

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        request_captured["headers"] = dict(request.headers)
        return httpx.Response(
            200,
            json={
                "id": "1122334455",
                "created_at": "2026-11-16T22:45:00.000Z",
                "url": "https://mastodon.social/@dxora_test/1122334455",
                "visibility": "public"
            }
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = MastodonPlatform(
        instance_url="https://mastodon.social",
        access_token="fake_mastodon_bearer_token",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Mastodon"
    assert result.status == "success"
    assert result.posted_url == "https://mastodon.social/@dxora_test/1122334455"
    assert result.public_access is True
    assert result.date == "2026-11-16"
    assert result.time == "22:45:00"
    assert result.error is None
    assert request_captured["headers"]["authorization"] == "Bearer fake_mastodon_bearer_token"


@pytest.mark.anyio
async def test_mastodon_api_error_handling():
    """Verify Mastodon 401 Unauthorized API error is handled gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": "The access token is invalid"}
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = MastodonPlatform(
        instance_url="https://mastodon.social",
        access_token="bad_token",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Mastodon"
    assert result.status == "failed"
    assert "Mastodon API error (HTTP 401): The access token is invalid" in result.error


@pytest.mark.anyio
async def test_mastodon_token_redaction_in_errors():
    """Verify that Mastodon access tokens are masked if included in errors."""
    secret_token = "SECRET_MASTODON_TOKEN_777"

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.RequestError(f"Connection failed while sending token {secret_token}")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = MastodonPlatform(
        instance_url="https://mastodon.social",
        access_token=secret_token,
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Mastodon"
    assert result.status == "failed"
    assert secret_token not in result.error
    assert "[REDACTED]" in result.error


@pytest.mark.anyio
async def test_mastodon_timeout():
    """Verify Mastodon handles network timeouts gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = MastodonPlatform(
        instance_url="https://mastodon.social",
        access_token="test_token",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Mastodon"
    assert result.status == "failed"
    assert result.error == "Mastodon request timed out"


# ---------------------------------------------------------
# Scenario 8: DEV.to Unit Tests (Mocked)
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_devto_missing_credentials():
    """Verify DEV.to fails safely when credentials are unconfigured."""
    platform = DevtoPlatform(api_key="")
    result = await platform.post("Test message https://example.com")

    assert result.platform == "DEV.to"
    assert result.status == "failed"
    assert result.posted_url is None
    assert result.public_access is False
    assert "credentials not configured" in result.error


@pytest.mark.anyio
async def test_devto_successful_publishing():
    """Verify DEV.to publishes an article, generates valid title/body, and parses URL/timestamp."""
    request_captured = {}

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        request_captured["headers"] = dict(request.headers)
        request_captured["json"] = json.loads(request.content)
        return httpx.Response(
            201,
            json={
                "id": 9876543,
                "title": "Check out our latest platform release",
                "url": "https://dev.to/zouatine_zakaria/check-out-our-latest-platform-release-9876543",
                "published": True,
                "published_at": "2026-11-16T23:15:30Z"
            }
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DevtoPlatform(
        api_key="fake_devto_api_key",
        client=mock_client
    )

    result = await platform.post("Check out our latest platform release! https://dxora.com")

    assert result.platform == "DEV.to"
    assert result.status == "success"
    assert result.posted_url == "https://dev.to/zouatine_zakaria/check-out-our-latest-platform-release-9876543"
    assert result.public_access is True
    assert result.date == "2026-11-16"
    assert result.time == "23:15:30"
    assert result.error is None
    assert request_captured["headers"]["api-key"] == "fake_devto_api_key"
    article_data = request_captured["json"]["article"]
    assert len(article_data["title"]) > 0
    assert len(article_data["title"]) <= 90
    assert article_data["body_markdown"] == "Check out our latest platform release! https://dxora.com"
    assert article_data["published"] is True


def test_devto_title_generation():
    """Verify DEV.to title extraction generates clean, non-empty titles within limits."""
    platform = DevtoPlatform(api_key="dummy")

    title1 = platform._generate_title("Exciting launch of our new developer tools! https://example.com")
    assert title1 == "Exciting launch of our new developer tools"

    title2 = platform._generate_title("Hi https://example.com")
    assert title2 == "New Platform Announcement"

    long_msg = "A" * 150 + " https://example.com"
    title3 = platform._generate_title(long_msg)
    assert len(title3) <= 90


@pytest.mark.anyio
async def test_devto_api_error_handling():
    """Verify DEV.to 422 Unprocessable Entity error is handled gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={"error": "Title has already been taken"}
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DevtoPlatform(
        api_key="fake_key",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "DEV.to"
    assert result.status == "failed"
    assert "DEV.to API error (HTTP 422): Title has already been taken" in result.error


@pytest.mark.anyio
async def test_devto_token_redaction_in_errors():
    """Verify that DEV.to API keys are masked in exception strings."""
    secret_key = "SECRET_DEVTO_KEY_999"

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.RequestError(f"Connection failed sending api-key {secret_key}")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DevtoPlatform(
        api_key=secret_key,
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "DEV.to"
    assert result.status == "failed"
    assert secret_key not in result.error
    assert "[REDACTED]" in result.error


@pytest.mark.anyio
async def test_devto_timeout():
    """Verify DEV.to handles network timeouts gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DevtoPlatform(
        api_key="test_key",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "DEV.to"
    assert result.status == "failed"
    assert result.error == "DEV.to request timed out"


# ---------------------------------------------------------
# Scenario 9: Discord Unit Tests (Mocked)
# ---------------------------------------------------------

@pytest.mark.anyio
async def test_discord_missing_credentials():
    """Verify Discord fails safely when credentials are unconfigured."""
    platform = DiscordPlatform(webhook_url="")
    result = await platform.post("Test message https://example.com")

    assert result.platform == "Discord"
    assert result.status == "failed"
    assert result.posted_url is None
    assert result.public_access is False
    assert "credentials not configured" in result.error


@pytest.mark.anyio
async def test_discord_successful_publishing():
    """Verify Discord posts with wait=true, parses timestamp, and sets posted_url=None, public_access=False."""
    request_captured = {}

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        request_captured["url"] = str(request.url)
        return httpx.Response(
            200,
            json={
                "id": "123456789012345678",
                "type": 0,
                "content": "Check out our launch! https://example.com",
                "channel_id": "987654321098765432",
                "timestamp": "2026-11-16T23:25:00.000000+00:00"
            }
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DiscordPlatform(
        webhook_url="https://discord.com/api/webhooks/123456789/fake_token_abc",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Discord"
    assert result.status == "success"
    # Clarification 1: Gated server, no reliable anonymous public URL
    assert result.posted_url is None
    assert result.public_access is False
    assert result.date == "2026-11-16"
    assert result.time == "23:25:00"
    assert result.error is None
    assert "wait=true" in request_captured["url"]


@pytest.mark.anyio
async def test_discord_api_error_handling():
    """Verify Discord 404 Unknown Webhook error is handled gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"message": "Unknown Webhook", "code": 10015}
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DiscordPlatform(
        webhook_url="https://discord.com/api/webhooks/123456789/invalid_token",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Discord"
    assert result.status == "failed"
    assert "Discord API error (HTTP 404): Unknown Webhook" in result.error


@pytest.mark.anyio
async def test_discord_token_redaction_in_errors():
    """Verify that complete Discord webhook URL and token are redacted from error strings."""
    secret_token = "SECRET_DISCORD_TOKEN_XYZ"
    webhook_url = f"https://discord.com/api/webhooks/123456789/{secret_token}"

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.RequestError(f"Connection failed for {webhook_url}?wait=true")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DiscordPlatform(
        webhook_url=webhook_url,
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Discord"
    assert result.status == "failed"
    # Clarification 2: The secret token and full URL with query parameters are scrubbed
    assert secret_token not in result.error
    assert "[REDACTED" in result.error


@pytest.mark.anyio
async def test_discord_timeout():
    """Verify Discord handles network timeouts gracefully."""
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    platform = DiscordPlatform(
        webhook_url="https://discord.com/api/webhooks/123/token",
        client=mock_client
    )

    result = await platform.post("Check out our launch! https://example.com")

    assert result.platform == "Discord"
    assert result.status == "failed"
    assert result.error == "Discord request timed out"
