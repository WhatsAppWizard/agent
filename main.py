import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiohttp
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer

from database import ConversationDB
from database_config import Base, engine

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
OPENROUTER_API_MODEL = os.getenv("OPENROUTER_API_MODEL")

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
        self.max_context_tokens = 4000

    def _count_tokens(self, text: str) -> int:
        """Estimate tokens in a given text using a character-based approach (for non-LLM specific parts)"""
        # A common estimation is ~4 characters per token for English text
        return len(text) // 4

    async def get_conversation_context(self, user_id: str) -> List[Dict]:
        """Get enhanced conversation context for a user, with token-based summarization"""
        context_messages = []
        current_tokens = 0
        
        # Add system prompt tokens to initial count
        system_prompt_template = """
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
        
        current_tokens += self._count_tokens(system_prompt_template)

        # Get user preferences
        preferences = await db.get_user_preferences(user_id)
        if preferences.get('preferred_language'):
            lang_pref_text = f"User's preferred language: {preferences['preferred_language']}"
            lang_pref_tokens = self._count_tokens(lang_pref_text)
            if current_tokens + lang_pref_tokens <= self.max_context_tokens:
                context_messages.append({"role": "system", "content": lang_pref_text})
                current_tokens += lang_pref_tokens

        if preferences.get('conversation_topics'):
            topics = preferences['conversation_topics']
            if topics:
                topics_text_parts = ["Frequently discussed topics:"]
                # Sort topics by frequency (assuming topics is a list of strings for now)
                # This part might need adjustment based on the actual structure of conversation_topics
                # For now, assuming it's a simple list of strings, so just iterate
                for topic_item in topics[:3]: # Limit to top 3 for brevity
                    topics_text_parts.append(f"- {topic_item}") # Assuming simple topic string, not dict with count
                
                topics_text = "\n".join(topics_text_parts)
                topics_tokens = self._count_tokens(topics_text)
                if current_tokens + topics_tokens <= self.max_context_tokens:
                    context_messages.append({"role": "system", "content": topics_text})
                    current_tokens += topics_tokens

        # Get relevant memories
        memories = await db.get_relevant_memories(user_id, [])
        if memories:
            memories_text = "\nRelevant context from previous conversations:\n" + "\n".join([f"- {m['content']}" for m in memories])
            memory_tokens = self._count_tokens(memories_text)
            if current_tokens + memory_tokens <= self.max_context_tokens:
                context_messages.append({"role": "system", "content": memories_text})
                current_tokens += memory_tokens
            else:
                logger.warning(f"Not all memories fit in context for user {user_id}")

        # Get recent conversations
        conversations = await db.get_recent_conversations(user_id, self.max_context_length * 2)
        conversations_for_context = []
        conversations_to_summarize = []

        for conv in reversed(conversations):
            user_msg = {"role": "user", "content": conv['message']}
            assistant_msg = {"role": "assistant", "content": conv['response']}
            
            user_msg_tokens = self._count_tokens(user_msg['content'])
            assistant_msg_tokens = self._count_tokens(assistant_msg['content'])
            total_conv_tokens = user_msg_tokens + assistant_msg_tokens

            if current_tokens + total_conv_tokens <= self.max_context_tokens:
                conversations_for_context.insert(0, assistant_msg)
                conversations_for_context.insert(0, user_msg)
                current_tokens += total_conv_tokens
            else:
                conversations_to_summarize.insert(0, conv)
        
        # If there are conversations to summarize, do it
        if len(conversations_to_summarize) >= self.context_summary_threshold:
            logger.info(f"Triggering summarization for user {user_id}")
            summary_text, summary_tokens = await self._summarize_and_store(user_id, conversations_to_summarize)
            
            # Add summary to context if it fits
            if current_tokens + summary_tokens <= self.max_context_tokens:
                context_messages.append({"role": "system", "content": f"Summary of previous conversations: {summary_text}"})
                current_tokens += summary_tokens
            else:
                logger.warning(f"Generated summary too large to fit in context for user {user_id}")

        # Combine system prompt, memories, and recent conversations
        final_context = []
        final_context.append({"role": "system", "content": system_prompt_template})
        final_context.extend(context_messages)
        final_context.extend(conversations_for_context)

        return final_context

    async def _summarize_and_store(self, user_id: str, conversations: List[Dict]) -> Tuple[str, int]:
        """Summarize old conversations and store as a user memory"""
        conversation_text = "\n".join([f"User: {c['message']}\nAssistant: {c['response']}" for c in conversations])
        
        summarization_prompt = f"""The following is a conversation history between a user and an AI assistant. Please summarize the key topics and outcomes of this conversation. Focus on important information that an AI assistant would need to remember for future interactions with this user. Be concise.

Conversation History:
{conversation_text}

Summary:"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/gitnasr",
                        "X-Title": "WhatsAppWizard - Summarizer"
                    },
                    json={
                        "model": OPENROUTER_API_MODEL,
                        "messages": [
                            {"role": "user", "content": summarization_prompt}
                        ],
                        "temperature": 0.3,
                        "stream": False,
                        "usage": {"include": True}
                    }
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    summary_content = result['choices'][0]['message']['content']
                    summary_tokens = result['usage']['total_tokens']
            
            # Store summary as a memory
            await db.add_memory(
                user_id=user_id,
                memory_type="summarization",
                content=summary_content,
                importance=0.7,
                embedding=model.encode([summary_content]).tolist()
            )
            logger.info(f"Successfully summarized {len(conversations)} conversations for user {user_id}. Tokens: {summary_tokens}")
            return summary_content, summary_tokens

        except Exception as e:
            logger.error(f"Error during summarization for user {user_id}: {str(e)}")
            return "", 0

    async def process_message(self, user_id: str, message: str, language: str) -> Dict:
        """Process a new message with enhanced memory features"""
        try:
            # Ensure the user exists
            await db.get_or_create_user(user_id)

            # Initialize topic
            topic = None

            # Generate embedding for the message
            try:
                message_embedding = model.encode([message])[0]
            except Exception as e:
                logger.error(f"Error generating embedding: {str(e)}")
                message_embedding = None
            
            # Check for repetition if we have an embedding
            is_repetition = False
            similar_conv = None
            if message_embedding is not None:
                try:
                    is_repetition, similar_conv = await db.check_repetition(
                        user_id, 
                        message_embedding.tolist(),
                        threshold=0.8
                    )
                except Exception as e:
                    logger.error(f"Error checking repetition: {str(e)}")
            
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
            try:
                context_messages = await self.get_conversation_context(user_id)
            except Exception as e:
                logger.error(f"Error getting conversation context: {str(e)}")
                context_messages = []
            
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

            # Get response from OpenRouter
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        OPENROUTER_API_URL,
                        headers={
                            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://github.com/gitnasr",  # Required by OpenRouter
                            "X-Title": "WhatsAppWizard"  # Optional but helpful
                        },
                        json={
                            "model": OPENROUTER_API_MODEL, # Use the correct dynamic model
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                *context_messages,  # Unpack context messages correctly
                                {"role": "user", "content": message}
                            ],
                            "temperature": 0.7,
                            "stream": False,  # We want a single response for summarization
                            "usage": {"include": True} # Request usage stats
                        }
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()
                        llm_response_content = result['choices'][0]['message']['content']
                        total_tokens_used = result['usage']['total_tokens'] # Extract total tokens
                        prompt_tokens_used = result['usage']['prompt_tokens']
                        completion_tokens_used = result['usage']['completion_tokens']
            except Exception as e:
                logger.error(f"Error calling OpenRouter API: {str(e)}")
                raise

            # Store the conversation with enhanced metadata
            try:
                await db.add_conversation(
                    user_id=user_id,
                    message=message,
                    response=llm_response_content,
                    language=language,
                    embedding=message_embedding.tolist(),
                    num_tokens=total_tokens_used,  # Pass total tokens used
                    topic=topic # Pass extracted topic
                )
            except Exception as e:
                logger.error(f"Error storing conversation: {str(e)}")
                # Continue even if storage fails

            # Update context with the new messages
            try:
                await db.update_user_context(user_id, "user", message)
                await db.update_user_context(user_id, "assistant", llm_response_content)
            except Exception as e:
                logger.error(f"Error updating context: {str(e)}")
                # Continue even if context update fails

            return {
                "response": llm_response_content,
                "is_repetition": False
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
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