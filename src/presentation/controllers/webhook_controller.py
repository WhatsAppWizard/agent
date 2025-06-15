import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.container import container
from src.application.dtos.message_dto import MessageRequest, MessageResponse
from src.application.use_cases import ProcessMessageUseCase

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class WebhookRequest(BaseModel):
    message: Dict[str, Any]
    user: Dict[str, Any]

class WebhookResponse(BaseModel):
    response: str
    is_repetition: bool = False
    similar_conversation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Dependency to get database session
async def get_session() -> AsyncSession:
    async for session in container.get_session():
        yield session

# Dependency to get use case
def get_process_message_use_case(session: AsyncSession = Depends(get_session)) -> ProcessMessageUseCase:
    return container.get_process_message_use_case(session)

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/", response_model=WebhookResponse)
async def webhook(
    request: WebhookRequest,
    use_case: ProcessMessageUseCase = Depends(get_process_message_use_case)
) -> WebhookResponse:
    """Process incoming webhook messages"""
    try:
        # Extract message and user data
        message_text = request.message.get("text", "")
        user_id = request.user.get("id", "")
        
        if not message_text or not user_id:
            raise HTTPException(status_code=400, detail="Missing message or user ID")
        
        # Detect language (you can implement your own language detection logic)
        language = "en"  # Default to English
        
        # Create DTO
        message_request = MessageRequest(
            user_id=user_id,
            message=message_text,
            language=language,
            metadata=request.message
        )
        
        # Process message using use case
        result = await use_case.execute(message_request)
        
        # Convert to response model
        return WebhookResponse(
            response=result.response,
            is_repetition=result.is_repetition,
            similar_conversation=result.similar_conversation,
            error=result.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") 