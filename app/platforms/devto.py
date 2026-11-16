from datetime import datetime, timezone
import re
from typing import Optional
import httpx
from app.config import settings
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class DevtoPlatform(BasePlatform):
    name: str = "DEV.to"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.devto_api_key
        raw_url = api_url if api_url is not None else settings.devto_api_url
        self.api_url = raw_url.rstrip("/") if raw_url else "https://dev.to/api"
        self.client = client

    # Mask API key in exception or error responses.
    def _sanitize(self, text: str) -> str:
        if not text:
            return ""
        if self.api_key and self.api_key in text:
            text = text.replace(self.api_key, "[REDACTED]")
        return text

    async def _get_client(self):
        if self.client:
            return self.client, False
        return httpx.AsyncClient(timeout=15.0), True

    def _generate_title(self, message: str) -> str:
        text_without_url = re.sub(r'https?://\S+', '', message).strip()
        clean_title = text_without_url.strip(" .,;:!?-")
        if len(clean_title) >= 5:
            return clean_title[:90].strip(" .,;:!?-")
        return "New Platform Announcement"

    async def post(self, message: str) -> PlatformPostResult:
        if self.should_fail:
            raise RuntimeError("Simulated DEV.to error")

        # 1. Check credentials
        if not self.api_key:
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="DEV.to credentials not configured (DEVTO_API_KEY missing)"
            )

        client, should_close = await self._get_client()
        try:
            # 2. Build article
            title = self._generate_title(message)
            body_markdown = message

            endpoint = f"{self.api_url}/articles"
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "article": {
                    "title": title,
                    "body_markdown": body_markdown,
                    "published": True
                }
            }

            response = await client.post(endpoint, headers=headers, json=payload)
            data = {}
            try:
                data = response.json()
            except Exception:
                pass

            if response.status_code not in (200, 201):
                raw_error = data.get("error", data.get("message", f"HTTP {response.status_code}"))
                sanitized_error = self._sanitize(str(raw_error))
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error=f"DEV.to API error (HTTP {response.status_code}): {sanitized_error}"
                )

            post_url = data.get("url")
            if not post_url:
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error="DEV.to response missing published article URL"
                )

            published_at_raw = data.get("published_at")
            if published_at_raw:
                try:
                    clean_dt = published_at_raw.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(clean_dt)
                except Exception:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")

            return PlatformPostResult(
                platform=self.name,
                status="success",
                posted_url=post_url,
                public_access=True,
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
                error="DEV.to request timed out"
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
                error=f"DEV.to error: {sanitized_err}"
            )
        finally:
            if should_close:
                await client.aclose()

