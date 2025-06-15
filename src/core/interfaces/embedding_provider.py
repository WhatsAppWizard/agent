from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    @abstractmethod
    async def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Encode a list of texts into embeddings.
        :param texts: List of strings to encode.
        :return: List of embeddings (list of floats).
        """
        pass 