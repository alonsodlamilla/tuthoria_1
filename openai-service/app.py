import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from contextlib import asynccontextmanager

from shared.templates.prompts import TEMPLATES
from services.db_client import DBClient
from services.chat_service import ChatService
from models.chat import Message, ChatResponse, ConversationHistory
from config.settings import get_settings, Settings
from logging_config import setup_logging

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events handler"""
    # Startup
    logger.info("Starting OpenAI service")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    yield

    # Shutdown
    logger.info("Shutting down OpenAI service")
    await db_client.close()


app = FastAPI(
    title="TuthorIA OpenAI Service",
    description="AI-powered educational assistant service",
    lifespan=lifespan,
)
settings = get_settings()

# Configure loguru for more detailed logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    level="DEBUG",  # Set this to INFO in production
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add(
    "logs/openai_service_detailed.log",
    rotation="10 MB",
    retention="1 week",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
logger.info("Initializing service clients")
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
    logger.info(f"Processing chat message for user {message.user_id}")
    try:
        # Get conversation history
        logger.debug("Fetching conversation history")
        history = await db_client.get_conversation_history(message.user_id)

        # Process with LangChain
        logger.debug("Processing message with LangChain")
        response = await chat_service.process_message(
            message.content, message.user_id, history
        )

        # Log conversation
        logger.debug("Storing conversation in DB")
        success = await db_client.log_conversation(
            message.user_id, message.content, response
        )
        if not success:
            logger.warning(f"Failed to log conversation for user {message.user_id}")

        logger.info(f"Successfully processed message for user {message.user_id}")
        return ChatResponse(response=response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{user_id}", response_model=ConversationHistory)
async def get_conversation(user_id: str, limit: int = 10):
    """Get conversation history for a user"""
    logger.info(f"Fetching conversation history for user {user_id}")
    try:
        messages = await db_client.get_conversation_history(user_id, limit)
        logger.debug(f"Retrieved {len(messages)} messages for user {user_id}")
        return ConversationHistory(messages=messages, user_id=user_id)
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check called")
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "openai_configured": bool(settings.OPENAI_API_KEY),
    }
