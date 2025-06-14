from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, Boolean, ForeignKey, ARRAY
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

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

# Define models
class User(Base):
    """Model for storing user information"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_active = Column(DateTime(timezone=True), default=datetime.utcnow)
    preferences = Column(JSON)

    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    context = relationship("UserContext", back_populates="user", uselist=False)

class Conversation(Base):
    """Model for storing conversation history"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    response = Column(String, nullable=False)
    language = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    message_metadata = Column(JSON)
    embedding = Column(ARRAY(Float))
    topic = Column(String)

    # Relationships
    user = relationship("User", back_populates="conversations")

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
            'topic': self.topic
        }

class UserContext(Base):
    """Model for storing user context and preferences"""
    __tablename__ = "user_context"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    context_messages = Column(JSON, default=list)  # List of messages with roles
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    preferred_language = Column(String)
    conversation_topics = Column(ARRAY(String))
    user_preferences = Column(JSON)
    context_window = Column(Integer, default=10)
    repetition_threshold = Column(Float, default=0.8)

    # Relationships
    user = relationship("User", back_populates="context")

    def add_message(self, role: str, content: str):
        """Add a message to the context"""
        if not self.context_messages:
            self.context_messages = []
        self.context_messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Keep only the last N messages based on context_window
        if len(self.context_messages) > self.context_window:
            self.context_messages = self.context_messages[-self.context_window:]

class UserMemory(Base):
    """Model for storing important user memories"""
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    memory_type = Column(String, nullable=False)  # e.g., "preference", "fact", "interaction"
    content = Column(Text, nullable=False)
    importance = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_accessed = Column(DateTime(timezone=True), default=datetime.utcnow)
    memory_metadata = Column(JSON)
    embedding = Column(ARRAY(Float))

    # Relationships
    user = relationship("User") 