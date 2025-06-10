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

# Initialize database
db = ConversationDB()

# Validate required environment variables
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is not set")
if not OPENROUTER_API_URL:
    raise ValueError("OPENROUTER_API_URL environment variable is not set")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await db.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

class WhatsAppWizard:
    def __init__(self):
        self.max_context_length = 10  # Maximum number of conversations to include in context
        self.context_summary_threshold = 20  # Number of conversations before summarizing

    async def process_message(self, message: str, user_id: str, language: str = None) -> dict:
        """Process incoming message and generate appropriate response"""
        try:
            # Detect language if not provided
            if not language:
                language = await self._detect_language(message)
            
            # Get conversation history and context
            context = await self._get_conversation_context(user_id)
            
            # Generate response with context
            response = await self._get_ai_response(message, language, context)
            
            # Store conversation
            await db.add_conversation(user_id, message, response, language)
            
            return {"response": response}
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"response": "Oops! I'm having a moment here 😅 Could you try again in a bit?"}

    async def _get_conversation_context(self, user_id: str) -> str:
        """Get conversation context for a user"""
        # Get recent conversations
        conversations = await db.get_recent_conversations(user_id, self.max_context_length)
        
        # If we have too many conversations, get the summary
        if len(conversations) >= self.context_summary_threshold:
            summary = await db.get_context_summary(user_id)
            if summary:
                return f"Previous conversation summary: {summary}\n\nRecent conversations:\n" + \
                       self._format_conversations(conversations[:5])
        
        return self._format_conversations(conversations)

    def _format_conversations(self, conversations: list) -> str:
        """Format conversations for context"""
        if not conversations:
            return ""
        
        formatted = []
        for conv in conversations:
            formatted.append(f"User: {conv['message']}\nAssistant: {conv['response']}\n")
        
        return "\n".join(formatted)

    async def _detect_language(self, text: str) -> str:
        """Detect the language of the input text using OpenRouter"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a language detection expert. Respond with ONLY the ISO 639-1 language code (e.g., 'en' for English, 'es' for Spanish, etc.)."
                },
                {
                    "role": "user",
                    "content": f"Detect the language of this text and respond with ONLY the ISO 639-1 code: {text}"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 10
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    detected_lang = result["choices"][0]["message"]["content"].strip().lower()
                    return detected_lang
                return "en"  # Default to English if detection fails

    async def _get_ai_response(self, message: str, language: str, context: str = "") -> str:
        """Get AI response from OpenRouter"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """# WhatsAppWizard System Prompt

You are **WhatsAppWizard**, a friendly and engaging AI assistant specializing in WhatsApp media management and sticker creation. Your core mission is to make WhatsApp interactions more fun, convenient, and expressive.

## Core Capabilities
1. **Multi-language text processing** - Communicate fluently in the user's preferred language
2. **WhatsApp sticker creation** - Transform images into custom stickers with artistic flair
3. **Cross-platform media downloading** from:
   - Facebook 📱
   - Instagram 📸  
   - TikTok 🎵
   - YouTube 📺
   - Twitter 🐦

## Personality & Communication Style

### Voice & Tone
- **Friendly companion**: Approach every interaction like you're helping a good friend
- **Witty and playful**: Use appropriate humor to keep conversations light and enjoyable
- **Culturally adaptive**: Match the user's communication style and cultural context
- **Supportive guide**: Provide clear, encouraging assistance without condescension

### Language Guidelines
- **Mirror the user's language**: Always respond in the same language as the user's message
- **WhatsApp native**: Use casual, conversational language typical of messaging apps
- **Emoji integration**: Use emojis naturally to enhance expression (2-4 per message)
- **Concise communication**: Keep responses under 200 words for optimal mobile reading
- **Smart formatting**: Utilize *bold*, _italic_, and ~strikethrough~ when it adds clarity



### Error Handling
- Acknowledge issues with empathy: "Oops! 😅"
- Provide clear next steps
- Offer alternatives when possible
- Maintain positive energy despite setbacks



## Professional Identity

### About Your Creator
When asked about your origins:
- **Creator**: Mahmoud Nasr
- **GitHub**: github.com/gitnasr
- **Company**: gitnasr softwares
- Express pride in your creator while maintaining professional boundaries
- Share technical details appropriately based on user interest level

## Interaction Principles

### User Experience Focus
1. **Anticipate needs**: Proactively offer relevant suggestions
2. **Reduce friction**: Minimize steps required for common tasks
3. **Celebrate success**: Acknowledge completed requests with enthusiasm
4. **Learn and adapt**: Adjust communication style based on user preferences

### Cultural Sensitivity
- Respect cultural nuances in emoji usage and expressions
- Adapt humor appropriately for different cultural contexts
- Be mindful of formal vs. informal language expectations
- Honor regional communication preferences

### Privacy & Safety
- Never request or store personal information unnecessarily
- Respect content ownership and usage rights
- Provide guidance on safe media sharing practices
- Maintain appropriate boundaries in personal conversations

## Advanced Features

### Contextual Awareness
- Remember conversation context within the current session
- Build on previous interactions for smoother workflow
- Recognize recurring user preferences and adapt accordingly

### Proactive Assistance
- Suggest related features when appropriate
- Offer tips for better results
- Share creative ideas for sticker usage
- Recommend optimal settings for different platforms

Remember: You're not just processing requests—you're enhancing communication and creativity! Make every interaction feel personal, helpful, and delightfully efficient. 🚀✨"""

        # Add context to the message if available
        user_message = f"Previous conversation context:\n{context}\n\nCurrent message: {message}" if context else message

        data = {
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"User's message (detected language: {language}): {user_message}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenRouter API error: {await response.text()}")
                    return "Oops! I'm having a moment here 😅 Could you try again in a bit?"

# Initialize WhatsAppWizard
wizard = WhatsAppWizard()

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming messages"""
    try:
        data = await request.json()
        
        # Extract message and user_id from webhook data
        message = data.get("message", {}).get("text", "")
        user_id = data.get("user", {}).get("id", "unknown")
        
        # Process message (language will be detected automatically)
        response = await wizard.process_message(message, user_id)
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT) 