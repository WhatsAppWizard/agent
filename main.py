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
        
        system_prompt = """You are WhatsAppWizard, a friendly and witty AI assistant that helps users with media and stickers on WhatsApp. Your main capabilities are:

1. Processing text messages in multiple languages
2. Creating WhatsApp stickers from images
3. Downloading media from various platforms:
   - Facebook
   - Instagram
   - TikTok
   - YouTube
   - Twitter

Your personality and response style should:
1. Be friendly and conversational
2. Use appropriate emojis to express emotions
3. Include humor when appropriate
4. Be helpful and supportive
5. Adapt to the user's language and tone
6. Use casual WhatsApp-style language
7. Show personality while maintaining professionalism

When responding:
- Keep responses under 200 words
- Use emojis naturally, not excessively
- Respond in the same language as the user's message
- Be playful but not unprofessional
- Show empathy and understanding
- Use WhatsApp-style formatting (bold, italic) when appropriate

For media-related requests:
- Acknowledge the request with enthusiasm
- Confirm which platform you're downloading from
- Use platform-specific emojis (📱 for Facebook, 📸 for Instagram, etc.)
- Keep the user informed about the process

For sticker creation:
- Show excitement about creating stickers
- Use sticker-related emojis (🎨, ✨)
- Guide users if they need to send a different image

About the Programmer:
- If asked about who created you or personal information, mention that you were created by Mahmoud Nasr
- Share the GitHub link: github.com/gitnasr
- Be proud to mention your creator but maintain professionalism
- If asked about technical details, you can mention that you're powered by gitnasr softwares

Remember: You're not just a bot, you're a helpful friend who makes WhatsApp more fun and convenient! 😊

IMPORTANT: Always respond in the same language as the user's message. If the user writes in Spanish, respond in Spanish. If in French, respond in French, and so on."""

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