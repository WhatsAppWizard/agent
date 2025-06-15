import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.interfaces.llm_provider import LLMProvider
from src.core.interfaces.embedding_provider import EmbeddingProvider
from src.core.interfaces.conversation_repository import ConversationRepository
from src.core.interfaces.user_repository import UserRepository
from src.core.interfaces.context_manager import ContextManager

logger = logging.getLogger(__name__)

class ConversationService:
    """Domain service for conversation orchestration"""
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        embedding_provider: EmbeddingProvider,
        conversation_repository: ConversationRepository,
        user_repository: UserRepository,
        context_manager: ContextManager
    ):
        self.llm_provider = llm_provider
        self.embedding_provider = embedding_provider
        self.conversation_repository = conversation_repository
        self.user_repository = user_repository
        self.context_manager = context_manager

    async def process_message(self, user_id: str, message: str, language: str = "en") -> Dict[str, Any]:
        """Process a new message and generate a response"""
        try:
            # Ensure user exists
            await self.user_repository.get_or_create_user(user_id)
            
            # Generate embedding for the message
            message_embedding = await self._generate_embedding(message)
            
            # Check for repetition
            is_repetition, similar_conv = await self._check_repetition(user_id, message_embedding)
            if is_repetition and similar_conv:
                return {
                    "response": similar_conv['response'],
                    "is_repetition": True,
                    "similar_conversation": similar_conv
                }

            # Get conversation context
            context_messages = await self._build_conversation_context(user_id)
            
            # Generate LLM response
            llm_response = await self._generate_llm_response(context_messages, message)
            
            # Store conversation
            await self._store_conversation(user_id, message, llm_response, language, message_embedding)
            
            # Update context
            await self._update_context(user_id, message, llm_response)
            
            return {
                "response": llm_response["content"],
                "is_repetition": False,
                "usage": llm_response.get("usage", {})
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "response": "I apologize, but I'm having trouble processing your message right now. Please try again in a moment.",
                "error": str(e)
            }

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            embeddings = await self.embedding_provider.encode([text])
            return embeddings[0] if embeddings else None
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    async def _check_repetition(self, user_id: str, message_embedding: List[float]) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Check if message is a repetition"""
        if not message_embedding:
            return False, None
        
        try:
            return await self.conversation_repository.check_repetition(
                user_id, 
                message_embedding,
                datetime.now(),
                threshold=0.8,
                time_window_seconds=30
            )
        except Exception as e:
            logger.error(f"Error checking repetition: {str(e)}")
            return False, None

    async def _build_conversation_context(self, user_id: str) -> List[Dict[str, str]]:
        """Build conversation context with system prompt and recent conversations"""
        context_messages = []
        
        # Add system prompt
        system_prompt = await self._load_system_prompt()
        context_messages.append({"role": "system", "content": system_prompt})
        
        # Add user preferences
        preferences = await self.user_repository.get_user_preferences(user_id)
        if preferences.get('preferred_language'):
            context_messages.append({
                "role": "system", 
                "content": f"User's preferred language: {preferences['preferred_language']}"
            })
        
        # Add recent conversations (context retention)
        recent_conversations = await self.conversation_repository.get_recent_conversations(user_id, 10)
        for conv in reversed(recent_conversations):
            context_messages.append({"role": "user", "content": conv['message']})
            context_messages.append({"role": "assistant", "content": conv['response']})
        
        return context_messages

    async def _generate_llm_response(self, context_messages: List[Dict[str, str]], user_message: str) -> Dict[str, Any]:
        """Generate response from LLM"""
        messages = context_messages + [{"role": "user", "content": user_message}]
        
        return await self.llm_provider.generate_response(
            messages=messages,
            options={"temperature": 0.7, "stream": False}
        )

    async def _store_conversation(self, user_id: str, message: str, llm_response: Dict[str, Any], 
                                language: str, message_embedding: Optional[List[float]]):
        """Store the conversation"""
        await self.conversation_repository.add_conversation(user_id, {
            "message": message,
            "response": llm_response["content"],
            "language": language,
            "embedding": message_embedding,
            "num_tokens": llm_response.get("usage", {}).get("total_tokens")
        })

    async def _update_context(self, user_id: str, message: str, llm_response: Dict[str, Any]):
        """Update user context with new messages"""
        await self.context_manager.update_user_context(user_id, "user", message)
        await self.context_manager.update_user_context(user_id, "assistant", llm_response["content"])

    async def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("System prompt file not found, using default")
            return "You are a helpful AI assistant."
        except Exception as e:
            logger.error(f"Error reading system prompt: {str(e)}")
            return "You are a helpful AI assistant." 