from datetime import datetime, timezone
import re
from typing import Optional
import httpx
from app.config import settings
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class TelegramPlatform(BasePlatform):
    name: str = "Telegram"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.bot_token = bot_token if bot_token is not None else settings.telegram_bot_token
        self.chat_id = chat_id if chat_id is not None else settings.telegram_chat_id
        self.client = client

    # Mask secret token in exception or error responses.
    def _sanitize(self, text: str) -> str:
        if not text:
            return ""
        if self.bot_token and self.bot_token in text:
            text = text.replace(self.bot_token, "[REDACTED]")
        return re.sub(r"/bot[^/]+/", "/bot[REDACTED]/", text)

    async def _get_client(self):
        if self.client:
            return self.client, False
        return httpx.AsyncClient(timeout=15.0), True

    async def post(self, message: str) -> PlatformPostResult:
        if self.should_fail:
            raise RuntimeError("Simulated Telegram error")

        # 1. Check credentials
        if not self.bot_token or not self.chat_id:
            return PlatformPostResult(
                platform=self.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error="Telegram credentials not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)"
            )

        client, should_close = await self._get_client()
        try:
            # 2. Call Telegram Bot API sending endpoint
            send_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message
            }

            response = await client.post(send_url, json=payload)
            data = {}
            try:
                data = response.json()
            except Exception:
                pass

            if response.status_code != 200 or not data.get("ok"):
                raw_desc = data.get("description", f"HTTP {response.status_code}")
                sanitized_desc = self._sanitize(str(raw_desc))
                return PlatformPostResult(
                    platform=self.name,
                    status="failed",
                    posted_url=None,
                    public_access=False,
                    date=None,
                    time=None,
                    error=f"Telegram API error (HTTP {response.status_code}): {sanitized_desc}"
                )

            result_obj = data.get("result", {})
            message_id = result_obj.get("message_id")
            chat = result_obj.get("chat", {})

            date_unix = result_obj.get("date")
            if date_unix:
                dt = datetime.fromtimestamp(date_unix, tz=timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")

            chat_username = chat.get("username")
            if chat_username and message_id:
                clean_username = chat_username.lstrip("@")
                posted_url = f"https://t.me/{clean_username}/{message_id}"
                public_access = True
            else:
                posted_url = None
                public_access = False

            return PlatformPostResult(
                platform=self.name,
                status="success",
                posted_url=posted_url,
                public_access=public_access,
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
                error="Telegram request timed out"
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
                error=f"Telegram error: {sanitized_err}"
            )
        finally:
            if should_close:
                await client.aclose()
