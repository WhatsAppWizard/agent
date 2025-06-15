from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a response from the LLM given a list of messages and options.
        :param messages: List of message dicts with 'role' and 'content'.
        :param options: Additional options for the LLM (e.g., temperature, model name).
        :return: Dict with response content and metadata.
        """
        pass 