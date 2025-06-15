import logging
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.context_manager import ContextManager
from src.infrastructure.database.models import UserContext

logger = logging.getLogger(__name__)

class SQLContextManager(ContextManager):
    """SQL implementation of ContextManager"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_context(self, user_id: str) -> List[Dict[str, Any]]:
        """Get the context messages for a user"""
        try:
            context = await self._get_or_create_user_context(user_id)
            return context.context_messages or []
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return []

    async def update_user_context(self, user_id: str, role: str, content: str) -> None:
        """Add a message to the user's context"""
        try:
            context = await self._get_or_create_user_context(user_id)
            context.add_message(role, content)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error updating user context: {str(e)}")

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