from abc import ABC, abstractmethod
from app.schemas import PlatformPostResult


class BasePlatform(ABC):
    #Abstract base class representing publishing platform.

    name: str = "Base Platform"
    should_fail: bool = False

    @abstractmethod
    async def post(self, message: str) -> PlatformPostResult:

        pass
