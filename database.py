import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from database_config import Base, Conversation, UserContext, UserMemory, DATABASE_URL, User

logger = logging.getLogger(__name__)

class ConversationDB:
    """Database operations for conversation management"""
    
    def __init__(self):
        """Initialize database connection"""
        self.engine = create_async_engine(
            DATABASE_URL,
            echo=True,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )

    async def init_db(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def _get_or_create_user(self, session: AsyncSession, user_id: str) -> None:
        """Get or create a user record"""
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(id=user_id)
            session.add(user)
            await session.commit()

    async def add_conversation(self, user_id: str, message: str, response: str, 
                             language: str, embedding: List[float] = None, 
                             metadata: Dict = None, topic: str = None) -> None:
        """Add a new conversation entry with enhanced context"""
        try:
            async with self.async_session() as session:
                # Ensure user exists
                await self._get_or_create_user(session, user_id)
                
                conversation = Conversation(
                    user_id=user_id,
                    message=message,
                    response=response,
                    language=language,
                    embedding=embedding,
                    message_metadata=metadata,
                    topic=topic
                )
                session.add(conversation)
                await session.commit()
        except Exception as e:
            logger.error(f"Error adding conversation: {str(e)}")
            raise

    async def check_repetition(self, user_id: str, new_message_embedding: List[float], 
                             threshold: float = 0.8) -> Tuple[bool, Optional[Dict]]:
        """Check if the message is similar to previous conversations"""
        try:
            async with self.async_session() as session:
                # Get recent conversations
                query = select(Conversation).where(
                    Conversation.user_id == user_id
                ).order_by(Conversation.timestamp.desc()).limit(10)
                
                result = await session.execute(query)
                recent_convs = result.scalars().all()
                
                if not recent_convs:
                    return False, None
                
                # Compare embeddings
                for conv in recent_convs:
                    if conv.embedding:
                        similarity = cosine_similarity(
                            [new_message_embedding],
                            [conv.embedding]
                        )[0][0]
                        
                        if similarity > threshold:
                            return True, conv.to_dict()
                
                return False, None
        except Exception as e:
            logger.error(f"Error checking repetition: {str(e)}")
            return False, None

    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user"""
        async with self.async_session() as session:
            query = select(Conversation).where(
                Conversation.user_id == user_id
            ).order_by(Conversation.timestamp.desc()).limit(limit)
            
            result = await session.execute(query)
            conversations = result.scalars().all()
            
            return [conv.to_dict() for conv in conversations]

    async def _get_or_create_user_context(self, session: AsyncSession, user_id: str) -> UserContext:
        """Get or create user context"""
        query = select(UserContext).where(UserContext.user_id == user_id)
        result = await session.execute(query)
        context = result.scalar_one_or_none()
        
        if not context:
            context = UserContext(user_id=user_id)
            session.add(context)
            await session.commit()
        
        return context

    async def get_user_context(self, user_id: str) -> List[Dict]:
        """Get the context messages for a user"""
        try:
            async with self.async_session() as session:
                context = await self._get_or_create_user_context(session, user_id)
                return context.context_messages or []
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return []

    async def update_user_context(self, user_id: str, role: str, content: str) -> None:
        """Add a message to the user's context"""
        try:
            async with self.async_session() as session:
                context = await self._get_or_create_user_context(session, user_id)
                context.add_message(role, content)
                await session.commit()
        except Exception as e:
            logger.error(f"Error updating user context: {str(e)}")

    async def clear_user_context(self, user_id: str) -> None:
        """Clear the user's context messages"""
        try:
            async with self.async_session() as session:
                context = await self._get_or_create_user_context(session, user_id)
                context.context_messages = []
                await session.commit()
        except Exception as e:
            logger.error(f"Error clearing user context: {str(e)}")

    async def get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences and settings"""
        try:
            async with self.async_session() as session:
                context = await self._get_or_create_user_context(session, user_id)
                return {
                    'preferred_language': context.preferred_language,
                    'conversation_topics': context.conversation_topics or [],
                    'user_preferences': context.user_preferences or {},
                    'context_window': context.context_window,
                    'repetition_threshold': context.repetition_threshold
                }
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}

    async def cleanup_old_conversations(self, days: int = 30) -> None:
        """Clean up conversations older than specified days"""
        try:
            async with self.async_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = delete(Conversation).where(Conversation.timestamp < cutoff_date)
                await session.execute(query)
                await session.commit()
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {str(e)}")

    async def get_relevant_memories(self, user_id: str, query_embedding: List[float], 
                                  limit: int = 5) -> List[Dict]:
        """Get memories relevant to the current context"""
        try:
            async with self.async_session() as session:
                query = select(UserMemory).where(
                    and_(
                        UserMemory.user_id == user_id,
                        UserMemory.is_active == True
                    )
                )
                result = await session.execute(query)
                memories = result.scalars().all()
                
                # Calculate similarity scores
                memory_scores = []
                for memory in memories:
                    if memory.embedding:
                        similarity = cosine_similarity(
                            [query_embedding],
                            [memory.embedding]
                        )[0][0]
                        memory_scores.append((memory, similarity))
                
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

    async def add_memory(self, user_id: str, memory_type: str, content: str, 
                        importance: float = 1.0, metadata: Dict = None,
                        embedding: List[float] = None) -> None:
        """Add a new memory for the user"""
        try:
            async with self.async_session() as session:
                # Ensure user exists
                await self._get_or_create_user(session, user_id)
                
                memory = UserMemory(
                    user_id=user_id,
                    memory_type=memory_type,
                    content=content,
                    importance=importance,
                    memory_metadata=metadata,
                    embedding=embedding
                )
                session.add(memory)
                await session.commit()
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise

# Initialize database
db = ConversationDB() 