import logging
from typing import List, Dict, Any

from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.memory_repository import MemoryRepository
from src.infrastructure.database.models import UserMemory

logger = logging.getLogger(__name__)

class SQLMemoryRepository(MemoryRepository):
    """SQL implementation of MemoryRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_memory(self, user_id: str, memory: Dict[str, Any]) -> None:
        """Add a new memory for the user"""
        try:
            memory_obj = UserMemory(
                user_id=user_id,
                memory_type=memory['memory_type'],
                content=memory['content'],
                importance=memory.get('importance', 1.0),
                memory_metadata=memory.get('metadata'),
                embedding=memory.get('embedding')
            )
            self.session.add(memory_obj)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise

    async def get_relevant_memories(self, user_id: str, query_embedding: List[float], 
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """Get memories relevant to the current context"""
        try:
            query = select(UserMemory).where(
                and_(
                    UserMemory.user_id == user_id,
                    UserMemory.is_active == True
                )
            )
            result = await self.session.execute(query)
            memories = result.scalars().all()
            
            # Calculate similarity scores
            memory_scores = []
            for memory in memories:
                if memory.embedding and len(memory.embedding) == len(query_embedding):
                    try:
                        similarity = cosine_similarity(
                            [query_embedding],
                            [memory.embedding]
                        )[0][0]
                        memory_scores.append((memory, similarity))
                    except Exception as e:
                        logger.warning(f"Error calculating similarity for memory {memory.id}: {str(e)}")
                        continue
            
            # Sort by similarity and importance
            memory_scores.sort(key=lambda x: (x[1] * x[0].importance), reverse=True)
            
            return [{
                'content': memory.content,
                'type': memory.memory_type,
                'importance': memory.importance,
                'similarity': score
            } for memory, score in memory_scores[:limit]]
        except Exception as e:
            logger.error(f"Error getting relevant memories: {str(e)}")
            return [] 