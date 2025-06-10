from typing import List, Dict, Optional
import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from database_config import async_session, Conversation, UserContext, Base, engine

logger = logging.getLogger(__name__)

class ConversationDB:
    async def init_db(self):
        """Initialize the database with required tables"""
        try:
            async with engine.begin() as conn:
                # Drop all tables first (optional, comment out if you want to keep existing data)
                # await conn.run_sync(Base.metadata.drop_all)
                
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    async def add_conversation(self, user_id: str, message: str, response: str, language: str, metadata: Dict = None):
        """Add a new conversation entry"""
        try:
            async with async_session() as session:
                conversation = Conversation(
                    user_id=user_id,
                    message=message,
                    response=response,
                    language=language,
                    message_metadata=metadata
                )
                session.add(conversation)
                await session.commit()
        except Exception as e:
            logger.error(f"Error adding conversation: {str(e)}")
            raise

    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user"""
        try:
            async with async_session() as session:
                query = select(Conversation).where(
                    Conversation.user_id == user_id
                ).order_by(
                    Conversation.timestamp.desc()
                ).limit(limit)
                
                result = await session.execute(query)
                conversations = result.scalars().all()
                
                return [{
                    'message': conv.message,
                    'response': conv.response,
                    'language': conv.language,
                    'timestamp': conv.timestamp,
                    'metadata': conv.message_metadata
                } for conv in conversations]
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []

    async def get_context_summary(self, user_id: str) -> Optional[str]:
        """Get the context summary for a user"""
        try:
            async with async_session() as session:
                query = select(UserContext).where(UserContext.user_id == user_id)
                result = await session.execute(query)
                context = result.scalar_one_or_none()
                return context.context_summary if context else None
        except Exception as e:
            logger.error(f"Error getting context summary: {str(e)}")
            return None

    async def update_context_summary(self, user_id: str, summary: str):
        """Update the context summary for a user"""
        try:
            async with async_session() as session:
                context = UserContext(
                    user_id=user_id,
                    context_summary=summary
                )
                await session.merge(context)
                await session.commit()
        except Exception as e:
            logger.error(f"Error updating context summary: {str(e)}")
            raise

    async def cleanup_old_conversations(self, days: int = 30):
        """Clean up conversations older than specified days"""
        try:
            async with async_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = delete(Conversation).where(Conversation.timestamp < cutoff_date)
                await session.execute(query)
                await session.commit()
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {str(e)}")
            raise 