import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_wizard")
    
    # OpenRouter API
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_api_url: str = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    openrouter_api_model: str = os.getenv("OPENROUTER_API_MODEL", "")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Embedding
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Memory
    max_context_length: int = int(os.getenv("MAX_CONTEXT_LENGTH", "10"))
    context_summary_threshold: int = int(os.getenv("CONTEXT_SUMMARY_THRESHOLD", "5"))
    max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
    
    # Repetition detection
    repetition_threshold: float = float(os.getenv("REPETITION_THRESHOLD", "0.8"))
    repetition_time_window: int = int(os.getenv("REPETITION_TIME_WINDOW", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 