from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
import logging
import time
from pydantic import BaseModel
from typing import Optional
from services.chat_service import ChatService
from handlers.webhook_handler import WebhookHandler

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = FastAPI()
chat_service = ChatService()
webhook_handler = WebhookHandler()


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    message_type: Optional[str] = "text"


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        start_time = time.time()
        message = request.message
        user_id = request.user_id
        message_type = request.message_type
        model = "gpt-4"

        # Get conversation history
        chat_service.get_or_create_history(user_id)

        # Get response from OpenAI
        response = await chat_service.send_message_to_openai(message, user_id)

        # Log user message
        conversation_id = chat_service.log_conversation(
            user_id=user_id,
            role="user",
            message=message,
            message_type=message_type,
            response_time=time.time() - start_time,
            model_version=model,
        )

        # Log assistant response
        chat_service.log_conversation(
            user_id=user_id,
            role="assistant",
            message=response,
            message_type=message_type,
            response_time=time.time() - start_time,
            model_version=model,
            conversation_id=conversation_id,
        )

        return {"response": response}

    except Exception as e:
        logger.error(f"Error en chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/whatsapp")
async def webhook_verify(
    hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None
):
    if hub_mode and hub_verify_token:
        if hub_mode == "subscribe" and hub_verify_token == os.getenv(
            "WHATSAPP_VERIFY_TOKEN"
        ):
            logger.info("WEBHOOK_VERIFIED")
            return int(hub_challenge)
        raise HTTPException(status_code=403, detail="Forbidden")
    raise HTTPException(status_code=400, detail="Invalid verification request")


@app.post("/whatsapp")
async def webhook(request: Request):
    try:
        # Parse incoming webhook data
        data = await request.json()
        if not data:
            logger.error("No data received")
            return "OK"

        # Extract message details
        entry = data["entry"][0]
        if "changes" not in entry:
            return "OK"

        value = entry["changes"][0]["value"]
        if "messages" not in value:
            return "OK"

        message = value["messages"][0]
        message_id = message.get("id")

        # Check for duplicate messages
        if webhook_handler.is_message_processed(message_id):
            return "OK"

        webhook_handler.mark_message_processed(message_id)
        user_id = message["from"]
        message_text = message["text"]["body"]

        try:
            # 1. Store incoming message in DB
            await chat_service.store_message(user_id, message_text, is_user=True)

            # 2. Send to OpenAI service for processing
            response = await chat_service.send_message_to_openai(message_text, user_id)
            
            # 3. Send WhatsApp response
            message_data = webhook_handler.create_message_body(user_id, response)
            webhook_handler.send_whatsapp_message(message_data)

            return "OK"
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Send error message to user
            error_data = webhook_handler.create_message_body(
                user_id,
                "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente."
            )
            webhook_handler.send_whatsapp_message(error_data)
            return "OK"

    except Exception as e:
        logger.error(f"Critical error in webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal error")


@app.get("/test")
async def test():
    return "API funcionando!"


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8501))
    uvicorn.run(app, host="0.0.0.0", port=port)
