from datetime import datetime, timezone
import re
from typing import Optional
import httpx
from app.config import settings
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class DiscordPlatform(BasePlatform):
    name: str = "Discord"

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.webhook_url = webhook_url if webhook_url is not None else settings.discord_webhook_url
        self.client = client

    # Mask secrets in exception or error responses.
    def _sanitize(self, text: str) -> str:
        if not text:
            return ""

        if self.webhook_url:
            clean_base = self.webhook_url.split("?")[0]
            text = text.replace(self.webhook_url, "[REDACTED_DISCORD_WEBHOOK_URL]")
            text = text.replace(clean_base, "[REDACTED_DISCORD_WEBHOOK_URL]")

            parts = clean_base.rstrip("/").split("/")
            if len(parts) >= 2:
                token = parts[-1]
                if token and len(token) > 5 and token in text:
                    text = text.replace(token, "[REDACTED]")

        text = re.sub(
            r"https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/[^\s\"'>]+",
            "[REDACTED_DISCORD_WEBHOOK_URL]",
            text,
            flags=re.IGNORECASE
        )
        return text

    async def _get_client(self):
        if self.client:
            return self.client, False
        return httpx.AsyncClient(timeout=15.0), True

    async def post(self, message: str) -> PlatformPostResult:
        if self.should_fail:
            raise RuntimeError("Simulated Discord error")

        # 1. Check credentials
        if not self.webhook_url:
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="Discord credentials not configured (DISCORD_WEBHOOK_URL missing)"
            )

        client, should_close = await self._get_client()
        try:
            # 2. receive the created message object
            separator = "&" if "?" in self.webhook_url else "?"
            endpoint = f"{self.webhook_url}{separator}wait=true"

            payload = {
                "content": message
            }

            # 3. Post to Discord 
            response = await client.post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json=payload
            )

            data = {}
            try:
                data = response.json()
            except Exception:
                pass

            if response.status_code != 200:
                raw_error = data.get("message", f"HTTP {response.status_code}")
                sanitized_error = self._sanitize(str(raw_error))
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error=f"Discord API error (HTTP {response.status_code}): {sanitized_error}"
                )

            timestamp_raw = data.get("timestamp")
            if timestamp_raw:
                try:
                    dt = datetime.fromisoformat(timestamp_raw)
                except Exception:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")

            # Discord channels require authentication and server membership to view. => public_access is False and no posted_url.
            return PlatformPostResult(
                platform=self.name,
                status="success",
                posted_url=None,
                public_access=False,
                date=date_str,
                time=time_str,
                error=None
            )

        except httpx.TimeoutException:
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="Discord request timed out"
            )
        except Exception as exc:
            sanitized_err = self._sanitize(str(exc))
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=f"Discord error: {sanitized_err}"
            )
        finally:
            if should_close:
                await client.aclose()

