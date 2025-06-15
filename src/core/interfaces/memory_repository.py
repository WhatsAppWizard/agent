from abc import ABC, abstractmethod
from typing import List, Dict, Any

class MemoryRepository(ABC):
    @abstractmethod
    async def add_memory(self, user_id: str, memory: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_relevant_memories(self, user_id: str, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        pass 