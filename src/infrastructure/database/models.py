import os
from datetime import datetime, timezone
from typing import List, Dict, Any

from dotenv import load_dotenv
from sqlalchemy import (ARRAY, JSON, Boolean, Column, DateTime, Float,
                        ForeignKey, Integer, String, Text)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

# Load environment variables
load_dotenv()

# Database URL from environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_wizard")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

class User(Base):
    """SQLAlchemy model for storing user information"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_active = Column(DateTime(timezone=True), default=func.now())
    preferences = Column(JSON)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    context = relationship("UserContext", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memories = relationship("UserMemory", back_populates="user", cascade="all, delete-orphan")

    def to_domain_model(self):
        """Convert to domain model"""
        from src.core.models.user import User as UserDomain
        return UserDomain(
            user_id=self.id,
            created_at=self.created_at,
            last_active=self.last_active,
            preferences=self.preferences
        )

class Conversation(Base):
    """SQLAlchemy model for storing conversation history"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    response = Column(String, nullable=False)
    language = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    message_metadata = Column(JSON)
    embedding = Column(ARRAY(Float))
    topic = Column(String)
    num_tokens = Column(Integer)

    # Relationships
    user = relationship("User", back_populates="conversations")

    def to_domain_model(self):
        """Convert to domain model"""
        from src.core.models.conversation import Conversation as ConversationDomain
        return ConversationDomain(
            id=self.id,
            user_id=self.user_id,
            message=self.message,
            response=self.response,
            language=self.language,
            timestamp=self.timestamp,
            metadata=self.message_metadata,
            embedding=self.embedding,
            topic=self.topic,
            num_tokens=self.num_tokens
        )

    def to_dict(self):
        """Convert conversation to dictionary with proper datetime handling"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'language': self.language,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'message_metadata': self.message_metadata,
            'embedding': self.embedding,
            'topic': self.topic,
            'num_tokens': self.num_tokens
        }

class UserContext(Base):
    """SQLAlchemy model for storing user context and preferences"""
    __tablename__ = "user_context"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    context_messages = Column(JSON, default=list)  # List of messages with roles
    last_updated = Column(DateTime(timezone=True), default=func.now())
    preferred_language = Column(String)
    conversation_topics = Column(ARRAY(String))
    user_preferences = Column(JSON)
    context_window = Column(Integer, default=10)
    repetition_threshold = Column(Float, default=0.8)

    # Relationships
    user = relationship("User", back_populates="context")

    def to_domain_model(self):
        """Convert to domain model"""
        from src.core.models.context import Context as ContextDomain
        return ContextDomain(
            user_id=self.user_id,
            context_messages=self.context_messages,
            last_updated=self.last_updated,
            preferred_language=self.preferred_language,
            conversation_topics=self.conversation_topics,
            user_preferences=self.user_preferences,
            context_window=self.context_window,
            repetition_threshold=self.repetition_threshold
        )

    def add_message(self, role: str, content: str):
        """Add a message to the context"""
        if not self.context_messages:
            self.context_messages = []
        self.context_messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        # Keep only the last N messages based on context_window
        if len(self.context_messages) > self.context_window:
            self.context_messages = self.context_messages[-self.context_window:]

class UserMemory(Base):
    """SQLAlchemy model for storing important user memories"""
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    memory_type = Column(String, nullable=False)  # e.g., "preference", "fact", "interaction"
    content = Column(Text, nullable=False)
    importance = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_accessed = Column(DateTime(timezone=True), default=func.now())
    memory_metadata = Column(JSON)
    embedding = Column(ARRAY(Float))
    is_active = Column(Boolean, default=True)  # Track if the memory is still active

    # Relationships
    user = relationship("User", back_populates="memories")

    def to_domain_model(self):
        """Convert to domain model"""
        from src.core.models.memory import Memory as MemoryDomain
        return MemoryDomain(
            id=self.id,
            user_id=self.user_id,
            memory_type=self.memory_type,
            content=self.content,
            importance=self.importance,
            created_at=self.created_at,
            last_accessed=self.last_accessed,
            metadata=self.memory_metadata,
            embedding=self.embedding,
            is_active=self.is_active
        ) 