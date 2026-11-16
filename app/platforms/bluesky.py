from datetime import datetime, timezone
from typing import Optional
import httpx
from app.config import settings
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class BlueskyPlatform(BasePlatform):
    name: str = "Bluesky"

    def __init__(
        self,
        handle: Optional[str] = None,
        app_password: Optional[str] = None,
        service_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.handle = handle if handle is not None else settings.bsky_handle
        self.app_password = app_password if app_password is not None else settings.bsky_app_password
        raw_service_url = service_url if service_url is not None else settings.bsky_service_url
        self.service_url = raw_service_url.rstrip("/") if raw_service_url else "https://bsky.social"
        self.client = client

    async def _get_client(self):
        if self.client:
            return self.client, False
        return httpx.AsyncClient(timeout=15.0), True

    async def post(self, message: str) -> PlatformPostResult:
        if self.should_fail:
            raise RuntimeError("Simulated Bluesky API connection failure")

        # 1. Check credentials
        if not self.handle or not self.app_password:
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="Bluesky credentials not configured (BSKY_HANDLE or BSKY_APP_PASSWORD missing)"
            )

        client, should_close = await self._get_client()
        try:
            # 2. Authentication and create session
            session_url = f"{self.service_url}/xrpc/com.atproto.server.createSession"
            session_res = await client.post(
                session_url,
                json={
                    "identifier": self.handle,
                    "password": self.app_password
                }
            )

            if session_res.status_code != 200:
                error_detail = "Authentication failed"
                try:
                    data = session_res.json()
                    error_detail = data.get("message", error_detail)
                except Exception:
                    pass
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error=f"Bluesky auth error (HTTP {session_res.status_code}): {error_detail}"
                )

            session_data = session_res.json()
            access_jwt = session_data.get("accessJwt")
            did = session_data.get("did")

            if not access_jwt or not did:
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error="Bluesky session response missing accessJwt or did"
                )

            # 3. Create post record
            now = datetime.now(timezone.utc)
            created_at_iso = now.isoformat().replace("+00:00", "Z")

            create_url = f"{self.service_url}/xrpc/com.atproto.repo.createRecord"
            post_payload = {
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": message,
                    "createdAt": created_at_iso
                }
            }

            post_res = await client.post(
                create_url,
                headers={"Authorization": f"Bearer {access_jwt}"},
                json=post_payload
            )

            if post_res.status_code != 200:
                error_detail = "Failed to create post record"
                try:
                    data = post_res.json()
                    error_detail = data.get("message", error_detail)
                except Exception:
                    pass
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error=f"Bluesky publishing error (HTTP {post_res.status_code}): {error_detail}"
                )

            post_data = post_res.json()
            uri = post_data.get("uri")
            if not uri:
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error="Bluesky response missing post AT URI"
                )

            rkey = uri.rstrip("/").split("/")[-1]
            public_url = f"https://bsky.app/profile/{self.handle}/post/{rkey}"

            return PlatformPostResult(
                platform=self.name,
                status="success",
                posted_url=public_url,
                public_access=True,
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
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
                error="Bluesky request timed out"
            )
        except Exception as exc:
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=f"Bluesky error: {str(exc)}"
            )
        finally:
            if should_close:
                await client.aclose()
