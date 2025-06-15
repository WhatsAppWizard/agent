from typing import List, Dict, Any

from src.core.interfaces.user_repository import UserRepository
from src.core.interfaces.conversation_repository import ConversationRepository
from src.application.dtos.message_dto import ConversationContext

class GetContextUseCase:
    """Use case for getting conversation context"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository

    async def execute(self, user_id: str, query: str = None) -> ConversationContext:
        """Execute the use case"""
        try:
            # Get user preferences
            user_preferences = await self.user_repository.get_user_preferences(user_id)
            
            # Get recent conversations
            recent_conversations = await self.conversation_repository.get_recent_conversations(user_id, 10)
            
            # Convert conversations to message format
            messages = []
            for conv in reversed(recent_conversations):
                messages.append({"role": "user", "content": conv['message']})
                messages.append({"role": "assistant", "content": conv['response']})
            
            return ConversationContext(
                messages=messages,
                user_preferences=user_preferences,
                relevant_memories=[],  # Empty since we removed memory system
                token_count=len(messages) * 10  # Rough estimate
            )
            
        except Exception as e:
            # Return empty context on error
            return ConversationContext(
                messages=[],
                user_preferences={},
                relevant_memories=[],
                token_count=0
            ) 