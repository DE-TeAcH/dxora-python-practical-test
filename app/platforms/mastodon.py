from datetime import datetime, timezone
from typing import Optional
import httpx
from app.config import settings
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class MastodonPlatform(BasePlatform):
    name: str = "Mastodon"

    def __init__(
        self,
        instance_url: Optional[str] = None,
        access_token: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.instance_url = instance_url if instance_url is not None else settings.mastodon_instance_url
        self.access_token = access_token if access_token is not None else settings.mastodon_access_token
        self.client = client

    # Mask secret token in exception or error responses.
    def _sanitize(self, text: str) -> str:
        if not text:
            return ""
        if self.access_token and self.access_token in text:
            text = text.replace(self.access_token, "[REDACTED]")
        return text

    async def _get_client(self):
        if self.client:
            return self.client, False
        return httpx.AsyncClient(timeout=15.0), True

    async def post(self, message: str) -> PlatformPostResult:
        if self.should_fail:
            raise RuntimeError("Simulated Mastodon error")

        # 1. Check credentials
        if not self.instance_url or not self.access_token:
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="Mastodon credentials not configured (MASTODON_INSTANCE_URL or MASTODON_ACCESS_TOKEN missing)"
            )

        base_url = self.instance_url.strip().rstrip("/")
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"

        client, should_close = await self._get_client()
        try:
            # 2. Call official Mastodon API endpoint 
            endpoint = f"{base_url}/api/v1/statuses"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "status": message,
                "visibility": "public" 
            }

            response = await client.post(endpoint, headers=headers, json=payload)
            data = {}
            try:
                data = response.json()
            except Exception:
                pass

            if response.status_code != 200:
                raw_error = data.get("error", f"HTTP {response.status_code}")
                sanitized_error = self._sanitize(str(raw_error))
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error=f"Mastodon API error (HTTP {response.status_code}): {sanitized_error}"
                )

            post_url = data.get("url")
            created_at_raw = data.get("created_at")

            if created_at_raw:
                try:
                    clean_dt = created_at_raw.replace("Z", "+00:00")
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
                error="Mastodon request timed out"
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
                error=f"Mastodon error: {sanitized_err}"
            )
        finally:
            if should_close:
                await client.aclose()
