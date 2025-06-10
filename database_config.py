from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
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
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSON)

class UserContext(Base):
    __tablename__ = "user_context"

    user_id = Column(String, primary_key=True)
    context_summary = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 