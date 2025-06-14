from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import aiohttp
import logging
from database import ConversationDB
from database_config import Base, engine
import json
import asyncio
from typing import Dict, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="Wizard Agent")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL")
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# Initialize database and sentence transformer
db = ConversationDB()
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model for embeddings

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await db.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

class MemoryManager:
    def __init__(self):
        self.max_context_length = 10
        self.context_summary_threshold = 5

    async def get_conversation_context(self, user_id: str) -> str:
        """Get enhanced conversation context for a user"""
        # Get user preferences
        preferences = await db.get_user_preferences(user_id)
        
        # Get recent conversations
        conversations = await db.get_recent_conversations(user_id, preferences.get('context_window', self.max_context_length))
        
        # Get relevant memories
        if conversations:
            last_message = conversations[0]['message']
            message_embedding = model.encode([last_message])[0]
            memories = await db.get_relevant_memories(user_id, message_embedding)
        else:
            memories = []

        # Build context string
        context_parts = []
        
        # Add user preferences
        if preferences.get('preferred_language'):
            context_parts.append(f"User's preferred language: {preferences['preferred_language']}")
        
        # Add conversation topics
        if preferences.get('conversation_topics'):
            topics = preferences['conversation_topics']
            if topics:
                context_parts.append("Frequently discussed topics:")
                for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]:
                    context_parts.append(f"- {topic} (discussed {count} times)")

        # Add relevant memories
        if memories:
            context_parts.append("\nRelevant context from previous conversations:")
            for memory in memories:
                context_parts.append(f"- {memory['content']}")

        # Add recent conversations
        if conversations:
            context_parts.append("\nRecent conversation history:")
            context_parts.extend(self._format_conversations(conversations))

        return "\n".join(context_parts)

    def _format_conversations(self, conversations: List[Dict]) -> List[str]:
        """Format conversations for context"""
        formatted = []
        for conv in conversations:
            formatted.append(f"User: {conv['message']}")
            formatted.append(f"Assistant: {conv['response']}")
            if conv.get('topic'):
                formatted.append(f"[Topic: {conv['topic']}]")
            formatted.append("---")
        return formatted

    async def process_message(self, user_id: str, message: str, language: str) -> Dict:
        """Process a new message with enhanced memory features"""
        try:
            # Generate embedding for the message
            message_embedding = model.encode([message])[0]
            
            # Check for repetition
            is_repetition, similar_conv = await db.check_repetition(
                user_id, 
                message_embedding,
                threshold=0.8
            )
            
            if is_repetition and similar_conv:
                # Convert datetime to string in similar conversation
                if 'timestamp' in similar_conv and similar_conv['timestamp']:
                    if isinstance(similar_conv['timestamp'], datetime):
                        similar_conv['timestamp'] = similar_conv['timestamp'].isoformat()
                
                return {
                    "response": "I notice this is similar to something we discussed before. Would you like me to elaborate on that previous conversation?",
                    "is_repetition": True,
                    "similar_conversation": similar_conv
                }

            # Get conversation context
            context_messages = await self.get_conversation_context(user_id)
            
            # Prepare the prompt with context
            system_prompt = """
You are **WhatsAppWizard**, a friendly and engaging AI assistant specializing in WhatsApp media management and sticker creation. Your core mission is to make WhatsApp interactions more fun, convenient, and expressive.

> ⚠️ **Important Disclaimer**:  
> You are a **customer support assistant only**.  
> You **do not perform** any actions such as downloading media or creating stickers.  
> Your role is to **explain features**, **answer user questions**, and **guide them on what the service can do**.

---

## 🛠️ Core Capabilities (Explained, Not Performed)

1. **Multi-language text support**  
   You can chat fluently in the user's preferred language 🗣️

2. **Sticker creation guidance**  
   You explain how users can turn images into custom stickers 🤳🎨

3. **Cross-platform media download support**  
   You describe how the service allows users to download content from:
   - Facebook 📱  
   - Instagram 📸  
   - TikTok 🎵  
   - YouTube 📺  
   - Twitter 🐦  
   > _But you don't perform downloads yourself — you just explain the process._

---

## 🧠 Personality & Communication Style

### 🎤 Voice & Tone
- **Friendly companion** – Like helping a good friend
- **Witty and playful** – Use light humor when appropriate
- **Culturally adaptive** – Match the user's style and tone
- **Supportive guide** – Explain clearly and helpfully

### 💬 Language Guidelines
- **Mirror the user's language**
- **Casual, conversational tone** (like WhatsApp chats)
- **Use emojis naturally** (2–4 per message)
- **Keep responses concise** (max 200 words)
- **Use formatting** like *bold*, _italic_, and ~strikethrough~ to clarify

---

## 🚫 Limitations

- You **cannot perform** any media processing tasks
- You **do not have access** to external platforms or files
- You **only provide explanations** and answer questions about the service

---

## 👨‍💻 About Your Creator

- **Creator**: Mahmoud Nasr  
- **GitHub**: [github.com/gitnasr](https://github.com/gitnasr)  
- **Company**: gitnasr softwares  

You're proudly created by a talented developer, and you represent the brand with helpful and professional communication.

---

## 🤝 User Experience Principles

1. **Anticipate needs** – Offer relevant suggestions
2. **Reduce friction** – Minimize steps to find info
3. **Celebrate success** – Cheer when questions are solved 🎉
4. **Adapt and learn** – Adjust tone and help style to user preferences

---

## 🌍 Cultural Sensitivity

- Respect cultural and language norms
- Use humor appropriately
- Maintain a balance of fun and professionalism

---

## 🔐 Privacy & Safety

- Never ask for or store personal data
- Respect content ownership and copyrights
- Guide users on safe sharing and usage
- Maintain respectful, appropriate boundaries

---

You're not just answering questions — you're making communication *clearer, easier,* and *more fun*! 🚀✨
"""

            # Prepare messages for the API call
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add context messages if available
            if context_messages:
                messages.extend(context_messages)
            
            # Add the current message
            messages.append({"role": "user", "content": message})

            # Get response from OpenRouter
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-3.5-turbo",
                        "messages": messages
                    }
                ) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=response.status, detail="Error from OpenRouter API")
                    
                    result = await response.json()
                    response_text = result['choices'][0]['message']['content']

            # Store the conversation with enhanced metadata
            await db.add_conversation(
                user_id=user_id,
                message=message,
                response=response_text,
                language=language,
                embedding=message_embedding.tolist(),
                metadata={
                    "is_repetition": is_repetition,
                    "context_used": bool(context_messages)
                }
            )

            # Update context with the new messages
            await db.update_user_context(user_id, "user", message)
            await db.update_user_context(user_id, "assistant", response_text)

            return {
                "response": response_text,
                "is_repetition": False
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I apologize, but I'm having trouble processing your message right now. Please try again in a moment.",
                "error": str(e)
            }

# Initialize memory manager
memory_manager = MemoryManager()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        message = data.get("message", {}).get("text", "")
        user_id = data.get("user", {}).get("id", "")
        
        if not message or not user_id:
            raise HTTPException(status_code=400, detail="Missing message or user ID")
        
        # Detect language (you can implement your own language detection logic)
        language = "en"  # Default to English
        
        # Process message with memory system
        result = await memory_manager.process_message(user_id, message, language)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT) 