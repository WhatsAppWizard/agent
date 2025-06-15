from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class ConversationRepository(ABC):
    @abstractmethod
    async def add_conversation(self, user_id: str, conversation: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def check_repetition(self, user_id: str, new_message_embedding: List[float], current_timestamp: datetime, threshold: float = 0.8, time_window_seconds: int = 30) -> (bool, Optional[Dict[str, Any]]):
        pass 