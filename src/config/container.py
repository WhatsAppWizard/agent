import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.infrastructure.database.connection import DatabaseManager
from src.infrastructure.external import OpenRouterLLMProvider, SentenceTransformerEmbeddingProvider
from src.infrastructure.repositories import (
    SQLUserRepository, 
    SQLConversationRepository, 
    SQLContextManager
)
from src.core.services import ConversationService
from src.application.use_cases import ProcessMessageUseCase, GetContextUseCase

logger = logging.getLogger(__name__)

class Container:
    """Dependency injection container"""
    
    def __init__(self):
        self._database_manager: DatabaseManager = None
        self._llm_provider: OpenRouterLLMProvider = None
        self._embedding_provider: SentenceTransformerEmbeddingProvider = None
        
        # Repository instances (will be created per session)
        self._user_repository: SQLUserRepository = None
        self._conversation_repository: SQLConversationRepository = None
        self._context_manager: SQLContextManager = None
        
        # Service instances
        self._conversation_service: ConversationService = None
        
        # Use case instances
        self._process_message_use_case: ProcessMessageUseCase = None
        self._get_context_use_case: GetContextUseCase = None

    async def initialize(self):
        """Initialize the container and all dependencies"""
        try:
            # Initialize database
            self._database_manager = DatabaseManager()
            await self._database_manager.init_db()
            
            # Initialize external providers
            self._llm_provider = OpenRouterLLMProvider()
            self._embedding_provider = SentenceTransformerEmbeddingProvider(settings.embedding_model)
            
            logger.info("Container initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing container: {str(e)}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session"""
        async for session in self._database_manager.get_session():
            yield session

    def get_repositories(self, session: AsyncSession):
        """Get repository instances for a session"""
        return {
            'user_repository': SQLUserRepository(session),
            'conversation_repository': SQLConversationRepository(session),
            'context_manager': SQLContextManager(session)
        }

    def get_conversation_service(self, session: AsyncSession) -> ConversationService:
        """Get conversation service with session-specific repositories"""
        repositories = self.get_repositories(session)
        
        return ConversationService(
            llm_provider=self._llm_provider,
            embedding_provider=self._embedding_provider,
            conversation_repository=repositories['conversation_repository'],
            user_repository=repositories['user_repository'],
            context_manager=repositories['context_manager']
        )

    def get_process_message_use_case(self, session: AsyncSession) -> ProcessMessageUseCase:
        """Get process message use case"""
        conversation_service = self.get_conversation_service(session)
        return ProcessMessageUseCase(conversation_service)

    def get_get_context_use_case(self, session: AsyncSession) -> GetContextUseCase:
        """Get get context use case"""
        repositories = self.get_repositories(session)
        
        return GetContextUseCase(
            user_repository=repositories['user_repository'],
            conversation_repository=repositories['conversation_repository']
        )

    async def close(self):
        """Close the container and cleanup resources"""
        if self._database_manager:
            await self._database_manager.close()
        logger.info("Container closed")

# Global container instance
container = Container() 