from datetime import datetime
from typing import Optional, List, Dict, Any

class Context:
    def __init__(self, user_id: str, context_messages: Optional[List[Dict[str, Any]]] = None, last_updated: Optional[datetime] = None, preferred_language: Optional[str] = None, conversation_topics: Optional[List[str]] = None, user_preferences: Optional[Dict[str, Any]] = None, context_window: int = 10, repetition_threshold: float = 0.8):
        self.user_id = user_id
        self.context_messages = context_messages or []
        self.last_updated = last_updated or datetime.utcnow()
        self.preferred_language = preferred_language
        self.conversation_topics = conversation_topics or []
        self.user_preferences = user_preferences or {}
        self.context_window = context_window
        self.repetition_threshold = repetition_threshold 