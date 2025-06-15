import logging
from typing import List

from sentence_transformers import SentenceTransformer

from src.core.interfaces.embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)

class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """SentenceTransformer implementation of EmbeddingProvider"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"Initialized SentenceTransformer with model: {model_name}")

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode a list of texts into embeddings"""
        try:
            # SentenceTransformer.encode returns numpy arrays, convert to lists
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            raise 