from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class MessageRequest:
    """DTO for incoming message requests"""
    user_id: str
    message: str
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class MessageResponse:
    """DTO for message responses"""
    response: str
    is_repetition: bool = False
    similar_conversation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class ConversationContext:
    """DTO for conversation context"""
    messages: list
    user_preferences: Dict[str, Any]
    relevant_memories: list
    token_count: int = 0 