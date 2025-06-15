import logging
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.user_repository import UserRepository
from src.infrastructure.database.models import User, UserContext

logger = logging.getLogger(__name__)

class SQLUserRepository(UserRepository):
    """SQL implementation of UserRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, user_id: str) -> None:
        """Get or create a user record"""
        try:
            # Use ON CONFLICT DO NOTHING to atomically create the user if they don't exist
            insert_stmt = insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=['id'])
            await self.session.execute(insert_stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error getting or creating user: {str(e)}")
            raise

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and settings"""
        try:
            # Get or create user context
            context = await self._get_or_create_user_context(user_id)
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

    async def _get_or_create_user_context(self, user_id: str) -> UserContext:
        """Get or create user context"""
        query = select(UserContext).where(UserContext.user_id == user_id)
        result = await self.session.execute(query)
        context = result.scalar_one_or_none()
        
        if not context:
            context = UserContext(user_id=user_id)
            self.session.add(context)
            await self.session.commit()
        
        return context 