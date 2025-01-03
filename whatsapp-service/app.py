import os
import time
from fastapi import FastAPI, Request, HTTPException, Response
import logging
import aiohttp
import asyncio
from contextlib import asynccontextmanager
import socket
from pydantic import BaseModel
from typing import Optional

from config import get_settings
from logging_config import setup_logging
from services.chat_service import ChatService
from handlers.webhook_handler import WebhookHandler

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting WhatsApp service")

    # Agregar estos logs de debug
    logger.debug(f"DB Service URL: {settings.build_service_url('db', '/health')}")
    logger.debug(f"OpenAI Service URL: {settings.build_service_url('openai', '/health')}")

    # Check services health on startup
    services = [("db", "/health"), ("openai", "/health")]

    health_results = []
    for service, path in services:
        url = settings.build_service_url(service, path)
        try:
            connector = aiohttp.TCPConnector(
                family=socket.AF_INET6,
                ssl=None,
            )
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=5) as response:
                    is_healthy = response.status == 200
                    health_results.append(is_healthy)
                    logger.info(
                        f"{service} service health check: {'healthy' if is_healthy else 'unhealthy'}"
                    )
        except Exception as e:
            logger.error(f"Failed to connect to {service} service: {str(e)}")
            health_results.append(False)

    if not all(health_results):
        logger.error("Not all required services are healthy")

    # Initialize services
    app.chat_service = ChatService()
    app.webhook_handler = WebhookHandler()
    yield
    # Cleanup
    await app.chat_service.close()
    await app.webhook_handler.close()
    logger.info("Shutting down WhatsApp service")


app = FastAPI(
    title="TuthorIA WhatsApp Service",
    description="WhatsApp integration service for TuthorIA educational assistant",
    version="1.0.0",
    lifespan=lifespan,
)


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

        # Store user message
        await app.chat_service.store_message(
            user_id=user_id,
            content=message,
            sender="user",
            message_type=message_type
        )

        # Get response from OpenAI
        response = await app.chat_service.send_message_to_openai(message, user_id)

        # Store assistant response
        await app.chat_service.store_message(
            user_id=user_id,
            content=response,
            sender="assistant",
            message_type=message_type,
        )

        return {"response": response}

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/whatsapp")
async def webhook_verify(request: Request):
    try:
        # Get parameters from the request
        hub_mode = request.query_params.get("hub.mode")
        hub_verify_token = request.query_params.get("hub.verify_token")
        hub_challenge = request.query_params.get("hub.challenge")

        if hub_mode and hub_verify_token:
            if (
                hub_mode == "subscribe"
                and hub_verify_token == settings.whatsapp_verify_token
            ):
                logger.info("WEBHOOK_VERIFIED")
                return Response(content=hub_challenge)
            raise HTTPException(status_code=403, detail="Forbidden")
        raise HTTPException(status_code=400, detail="Invalid verification request")
    except Exception as e:
        logger.error(f"Error in webhook verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/whatsapp")
async def webhook(request: Request):
    try:
        data = await request.json()
        idempotency_key = request.headers.get("X-FB-Request-Id")

        if idempotency_key and app.webhook_handler.is_request_processed(
            idempotency_key
        ):
            logger.info(f"Skipping duplicate request {idempotency_key}")
            return Response(status_code=200)

        if not data or "entry" not in data:
            return Response(status_code=200)

        for entry in data["entry"]:
            if "changes" not in entry:
                continue

            for change in entry["changes"]:
                value = change.get("value", {})
                if "statuses" in value or "messages" not in value:
                    continue

                for message in value["messages"]:
                    if not app.webhook_handler.should_process_message(message):
                        continue

                    message_id = message["id"]
                    try:
                        user_id = message["from"]
                        message_text = message["text"]["body"]

                        # Store user message
                        await app.chat_service.store_message(
                            user_id=user_id,
                            content=message_text,
                            sender="user",
                            message_type="text",
                        )

                        # Get AI response
                        response = await app.chat_service.send_message_to_openai(
                            message_text, user_id
                        )

                        if response:
                            # Store AI response
                            await app.chat_service.store_message(
                                user_id=user_id,
                                content=response,
                                sender="assistant",
                                message_type="text",
                            )

                            # Send response back to user
                            message_data = app.webhook_handler.create_message_body(
                                user_id, response
                            )
                            success = await app.webhook_handler.send_whatsapp_message(
                                message_data
                            )

                            if success:
                                app.webhook_handler.mark_message_processed(
                                    message_id, response
                                )
                            else:
                                logger.error(
                                    f"Failed to send response for message {message_id}"
                                )

                    except Exception as e:
                        logger.error(
                            f"Error processing message {message_id}: {str(e)}",
                            exc_info=True,
                        )
                        app.webhook_handler.mark_message_processed(message_id)
                        error_data = app.webhook_handler.create_message_body(
                            user_id,
                            "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente.",
                        )
                        await app.webhook_handler.send_whatsapp_message(error_data)

        return Response(status_code=200)

    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health():
    logger.info("Health check called")
    try:
        return {"status": "healthy", "timestamp": time.time()}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service Unavailable")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8501))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="::", port=port, log_level="info")
