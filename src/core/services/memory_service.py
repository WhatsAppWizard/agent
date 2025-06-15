import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.interfaces.memory_repository import MemoryRepository
from src.core.interfaces.embedding_provider import EmbeddingProvider
from src.core.interfaces.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class MemoryService:
    """Domain service for memory management"""
    
    def __init__(
        self,
        memory_repository: MemoryRepository,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider
    ):
        self.memory_repository = memory_repository
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider

    async def add_memory(self, user_id: str, memory_type: str, content: str, 
                        importance: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a new memory for the user"""
        try:
            # Generate embedding for the memory content
            embedding = await self._generate_embedding(content)
            
            await self.memory_repository.add_memory(user_id, {
                "memory_type": memory_type,
                "content": content,
                "importance": importance,
                "metadata": metadata,
                "embedding": embedding
            })
            
            logger.info(f"Added memory for user {user_id}: {memory_type}")
            
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise

    async def get_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get memories relevant to a query"""
        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query)
            
            if not query_embedding:
                return []
            
            return await self.memory_repository.get_relevant_memories(user_id, query_embedding, limit)
            
        except Exception as e:
            logger.error(f"Error getting relevant memories: {str(e)}")
            return []

    async def summarize_conversations(self, user_id: str, conversations: List[Dict[str, Any]]) -> str:
        """Summarize conversations and store as memory"""
        try:
            if not conversations:
                return ""
            
            # Create summarization prompt
            conversation_text = "\n".join([
                f"User: {c['message']}\nAssistant: {c['response']}" 
                for c in conversations
            ])
            
            summarization_prompt = f"""The following is a conversation history between a user and an AI assistant. Please summarize the key topics and outcomes of this conversation. Focus on important information that an AI assistant would need to remember for future interactions with this user. Be concise.

Conversation History:
{conversation_text}

Summary:"""
            
            # Generate summary using LLM
            response = await self.llm_provider.generate_response(
                messages=[{"role": "user", "content": summarization_prompt}],
                options={"temperature": 0.3, "stream": False}
            )
            
            summary_content = response["content"]
            
            # Store summary as memory
            await self.add_memory(
                user_id=user_id,
                memory_type="summarization",
                content=summary_content,
                importance=0.7
            )
            
            logger.info(f"Successfully summarized {len(conversations)} conversations for user {user_id}")
            return summary_content
            
        except Exception as e:
            logger.error(f"Error summarizing conversations: {str(e)}")
            return ""

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            embeddings = await self.embedding_provider.encode([text])
            return embeddings[0] if embeddings else None
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None 