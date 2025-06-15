import logging
import os
from typing import List, Dict, Any

import aiohttp
from dotenv import load_dotenv

from src.core.interfaces.llm_provider import LLMProvider

load_dotenv()

logger = logging.getLogger(__name__)

class OpenRouterLLMProvider(LLMProvider):
    """OpenRouter implementation of LLMProvider"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        self.default_model = os.getenv("OPENROUTER_API_MODEL")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        if not self.default_model:
            raise ValueError("OPENROUTER_API_MODEL environment variable is required")

    async def generate_response(self, messages: List[Dict[str, str]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a response from OpenRouter API"""
        options = options or {}
        
        try:
            async with aiohttp.ClientSession() as session:
                request_payload = {
                    "model": options.get("model", self.default_model),
                    "messages": messages,
                    "temperature": options.get("temperature", 0.7),
                    "stream": options.get("stream", False),
                    "usage": {"include": True}
                }
                
                async with session.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/gitnasr",
                        "X-Title": "WhatsAppWizard"
                    },
                    json=request_payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    return {
                        "content": result['choices'][0]['message']['content'],
                        "usage": result.get('usage', {}),
                        "model": result.get('model'),
                        "finish_reason": result['choices'][0].get('finish_reason')
                    }
                    
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {str(e)}")
            raise 