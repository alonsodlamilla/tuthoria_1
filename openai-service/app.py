import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
import os
from datetime import datetime

from services.db_client import DBClient
from services.chat_service import ChatService
from shared.templates.prompts import TEMPLATES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenAI Service", description="AI Chat Service with state management"
)
db_client = DBClient()
chat_service = ChatService()


class Message(BaseModel):
    content: str
    user_id: str
    context: Optional[Dict[str, str]] = None


@app.post("/chat")
async def chat_endpoint(message: Message):
    try:
        # Get context
        context = await db_client.get_context(message.user_id)
        
        
        # Process message with ChatService
        response = await chat_service.process_message(
            message.content,
            context
        )
        
        # Log conversation
        await db_client.log_conversation(
            message.user_id,
            message.content,
            response
        )

        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str, limit: int = 10):
    try:
        conversations = await db_client.get_conversation_history(user_id, limit)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8502))
    uvicorn.run(app, host="0.0.0.0", port=port)
