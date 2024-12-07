from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from shared.templates.prompts import TEMPLATES
from services.db_client import DBClient
from services.chat_service import ChatService
from models.chat import Message, ChatResponse, ConversationHistory
from config.settings import get_settings, Settings

app = FastAPI(
    title="TuthorIA OpenAI Service",
    description="AI-powered educational assistant service"
)
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
db_client = DBClient()
chat_service = ChatService()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: Message):
    """
    Process a chat message through the following steps:
    1. Get conversation history from DB
    2. Generate AI response using LangChain
    3. Store conversation in DB
    4. Return response
    """
    try:
        # Get conversation history
        history = await db_client.get_conversation_history(message.user_id)
        
        # Process with LangChain
        response = await chat_service.process_message(
            message.content,
            message.user_id,
            history
        )
        
        # Log conversation
        success = await db_client.log_conversation(
            message.user_id,
            message.content,
            response
        )
        if not success:
            logger.warning(f"Failed to log conversation for user {message.user_id}")
        
        return ChatResponse(response=response)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{user_id}", response_model=ConversationHistory)
async def get_conversation(user_id: str, limit: int = 10):
    """Get conversation history for a user"""
    try:
        messages = await db_client.get_conversation_history(user_id, limit)
        return ConversationHistory(messages=messages, user_id=user_id)
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await db_client.close()
