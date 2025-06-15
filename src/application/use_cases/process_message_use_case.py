from typing import Dict, Any

from src.application.dtos.message_dto import MessageRequest, MessageResponse
from src.core.services.conversation_service import ConversationService

class ProcessMessageUseCase:
    """Use case for processing user messages"""
    
    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service

    async def execute(self, request: MessageRequest) -> MessageResponse:
        """Execute the use case"""
        try:
            # Process the message using the conversation service
            result = await self.conversation_service.process_message(
                user_id=request.user_id,
                message=request.message,
                language=request.language or "en"
            )
            
            # Convert to response DTO
            return MessageResponse(
                response=result["response"],
                is_repetition=result.get("is_repetition", False),
                similar_conversation=result.get("similar_conversation"),
                error=result.get("error")
            )
            
        except Exception as e:
            return MessageResponse(
                response="I apologize, but I'm having trouble processing your message right now. Please try again in a moment.",
                error=str(e)
            ) 