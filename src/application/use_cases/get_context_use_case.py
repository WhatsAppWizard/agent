from typing import List, Dict, Any

from src.core.interfaces.user_repository import UserRepository
from src.core.interfaces.memory_repository import MemoryRepository
from src.core.interfaces.conversation_repository import ConversationRepository
from src.core.interfaces.embedding_provider import EmbeddingProvider
from src.application.dtos.message_dto import ConversationContext

class GetContextUseCase:
    """Use case for getting conversation context"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        memory_repository: MemoryRepository,
        conversation_repository: ConversationRepository,
        embedding_provider: EmbeddingProvider
    ):
        self.user_repository = user_repository
        self.memory_repository = memory_repository
        self.conversation_repository = conversation_repository
        self.embedding_provider = embedding_provider

    async def execute(self, user_id: str, query: str = None) -> ConversationContext:
        """Execute the use case"""
        try:
            # Get user preferences
            user_preferences = await self.user_repository.get_user_preferences(user_id)
            
            # Get relevant memories
            relevant_memories = []
            if query:
                query_embedding = await self._generate_embedding(query)
                if query_embedding:
                    relevant_memories = await self.memory_repository.get_relevant_memories(
                        user_id, query_embedding, limit=5
                    )
            
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
                relevant_memories=relevant_memories,
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

    async def _generate_embedding(self, text: str):
        """Generate embedding for text"""
        try:
            embeddings = await self.embedding_provider.encode([text])
            return embeddings[0] if embeddings else None
        except Exception:
            return None 