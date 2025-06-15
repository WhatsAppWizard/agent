from abc import ABC, abstractmethod
from typing import Dict, Any

class UserRepository(ABC):
    @abstractmethod
    async def get_or_create_user(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        pass 