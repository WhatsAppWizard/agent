from datetime import datetime
from typing import Optional, Dict, Any, List

class Conversation:
    def __init__(self, id: int, user_id: str, message: str, response: str, language: str, timestamp: Optional[datetime] = None, metadata: Optional[Dict[str, Any]] = None, embedding: Optional[List[float]] = None, topic: Optional[str] = None, num_tokens: Optional[int] = None):
        self.id = id
        self.user_id = user_id
        self.message = message
        self.response = response
        self.language = language
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}
        self.embedding = embedding
        self.topic = topic
        self.num_tokens = num_tokens 