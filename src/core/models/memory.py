from datetime import datetime
from typing import Optional, Dict, Any, List

class Memory:
    def __init__(self, id: int, user_id: str, memory_type: str, content: str, importance: float = 1.0, created_at: Optional[datetime] = None, last_accessed: Optional[datetime] = None, metadata: Optional[Dict[str, Any]] = None, embedding: Optional[List[float]] = None, is_active: bool = True):
        self.id = id
        self.user_id = user_id
        self.memory_type = memory_type
        self.content = content
        self.importance = importance
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed = last_accessed or datetime.utcnow()
        self.metadata = metadata or {}
        self.embedding = embedding
        self.is_active = is_active 