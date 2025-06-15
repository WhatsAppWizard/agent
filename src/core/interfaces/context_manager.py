from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ContextManager(ABC):
    @abstractmethod
    async def get_user_context(self, user_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update_user_context(self, user_id: str, role: str, content: str) -> None:
        pass 