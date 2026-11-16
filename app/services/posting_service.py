from typing import List, Optional
from app.platforms import (
    BasePlatform,
    BlueskyPlatform,
    TelegramPlatform,
    MastodonPlatform,
    DevtoPlatform,
    DiscordPlatform,
)
from app.schemas import PlatformPostResult, PostingResponse


class PostingService:
    def __init__(self, platforms: Optional[List[BasePlatform]] = None):
        if platforms is not None:
            self.platforms = platforms
        else:
            self.platforms = [
                BlueskyPlatform(),
                TelegramPlatform(),
                MastodonPlatform(),
                DevtoPlatform(),
                DiscordPlatform(),
            ]

    async def post_to_platform(
        self,
        platform: BasePlatform,
        message: str
    ) -> PlatformPostResult:
        try:
            return await platform.post(message)
        except Exception as exc:
            # Prevent error from stopping other platforms
            return PlatformPostResult(
                platform=platform.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=str(exc)
            )

    async def post_to_all(self, message: str) -> PostingResponse:
        results: List[PlatformPostResult] = []

        for platform in self.platforms:
            result = await self.post_to_platform(platform, message)
            results.append(result)

        # at least one platform success
        overall_success = any(r.status == "success" for r in results)

        return PostingResponse(
            success=overall_success,
            results=results
        )
