from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Automated Multi-Platform Posting System"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 4000

    bsky_handle: Optional[str] = None
    bsky_app_password: Optional[str] = None
    bsky_service_url: str = "https://bsky.social"

    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    mastodon_instance_url: Optional[str] = None
    mastodon_access_token: Optional[str] = None

    devto_api_key: Optional[str] = None
    devto_api_url: str = "https://dev.to/api"

    discord_webhook_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
