import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.conversation_repository import ConversationRepository
from src.infrastructure.database.models import Conversation

logger = logging.getLogger(__name__)

class SQLConversationRepository(ConversationRepository):
    """SQL implementation of ConversationRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_conversation(self, user_id: str, conversation: Dict[str, Any]) -> None:
        """Add a new conversation entry"""
        try:
            conv = Conversation(
                user_id=user_id,
                message=conversation['message'],
                response=conversation['response'],
                language=conversation['language'],
                embedding=conversation.get('embedding'),
                message_metadata=conversation.get('metadata'),
                topic=conversation.get('topic'),
                num_tokens=conversation.get('num_tokens')
            )
            self.session.add(conv)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding conversation: {str(e)}")
            raise

    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations for a user"""
        try:
            query = select(Conversation).where(
                Conversation.user_id == user_id
            ).order_by(Conversation.timestamp.desc()).limit(limit)
            
            result = await self.session.execute(query)
            conversations = result.scalars().all()
            
            return [conv.to_dict() for conv in conversations]
        except Exception as e:
            logger.error(f"Error getting recent conversations: {str(e)}")
            return []

    async def check_repetition(self, user_id: str, new_message_embedding: List[float], 
                             current_timestamp: datetime, threshold: float = 0.8, 
                             time_window_seconds: int = 30) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if the message is similar to previous conversations within a time window"""
        try:
            time_threshold = current_timestamp - timedelta(seconds=time_window_seconds)

            # Get recent conversations within the time window
            query = select(Conversation).where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.timestamp >= time_threshold
                )
            ).order_by(Conversation.timestamp.desc()).limit(10)
            
            result = await self.session.execute(query)
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