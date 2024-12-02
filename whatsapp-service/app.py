from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
import requests
import logging
import time
from pymongo import MongoClient
from shared.templates import PROMPT_TEMPLATE
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# MongoDB setup
mongo_uri = f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}/"
mongo_client = MongoClient(mongo_uri)
db = mongo_client.whatsapp_db
conversations = db.conversations

# Diccionario para mantener el historial de conversaciones
conversation_history = {}

# Set para almacenar IDs de mensajes procesados
processed_messages = set()


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_id: str
    message_type: Optional[str] = "text"


class ChatResponse(BaseModel):
    response: str


class WhatsAppVerification(BaseModel):
    hub_mode: Optional[str] = None
    hub_verify_token: Optional[str] = None
    hub_challenge: Optional[str] = None


def send_message_to_openai(message, number):
    try:
        openai_service_url = os.getenv("OPENAI_SERVICE_URL")
        if not openai_service_url:
            raise ValueError("OPENAI_SERVICE_URL not configured")

        response = requests.post(
            f"{openai_service_url}/chat", json={"message": message, "user_id": number}
        )

        if response.status_code == 200:
            return response.json()["response"]
        else:
            logger.error(f"Error from OpenAI service: {response.text}")
            return "Lo siento, hubo un error al procesar tu mensaje."

    except Exception as e:
        logger.error(f"Error in send_message_to_openai: {str(e)}")
        return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"


def log_conversation(
    user_id,
    role,
    message,
    message_type="text",
    tokens_used=0,
    response_time=0,
    model_version="gpt-4",
    conversation_id=None,
):
    """Registrar conversación en MongoDB"""
    try:
        conversation_doc = {
            "user_id": user_id,
            "role": role,
            "message": message,
            "message_type": message_type,
            "tokens_used": tokens_used,
            "response_time": response_time,
            "model_version": model_version,
            "timestamp": time.time(),
            "conversation_id": conversation_id,
        }
        result = conversations.insert_one(conversation_doc)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error registrando en MongoDB: {str(e)}")
        return None


def get_conversation_history(user_id, limit=20):
    """Obtener historial de conversaciones de MongoDB"""
    try:
        return list(
            conversations.find(
                {"user_id": user_id}, {"_id": 0, "message": 1, "role": 1}
            )
            .sort("timestamp", -1)
            .limit(limit)
        )
    except Exception as e:
        logger.error(f"Error obteniendo historial de conversaciones: {str(e)}")
        return []


def whatsapp_service(body):
    """Envía mensaje a WhatsApp"""
    try:
        token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        api_url = os.getenv("WHATSAPP_API_URL")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        response = requests.post(api_url, headers=headers, json=body)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en WhatsApp API: {response.text}")
            return None
    except Exception as e:
        print(f"Error en whatsapp_service: {str(e)}")
        return None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        start_time = time.time()
        message = request.message
        user_id = request.user_id
        message_type = request.message_type
        model = "gpt-4"

        # Obtener historial reciente de MongoDB
        recent_history = get_conversation_history(user_id, limit=20)

        # Inicializar historial si no existe
        if user_id not in conversation_history:
            conversation_history[user_id] = [
                {"role": "system", "content": PROMPT_TEMPLATE}
            ]

        # Agregar mensaje del usuario al historial
        conversation_history[user_id].append({"role": "user", "content": message})

        # Obtener respuesta de OpenAI
        response = send_message_to_openai(message, user_id)

        # Registrar mensaje del usuario
        conversation_id = log_conversation(
            user_id=user_id,
            role="user",
            message=message,
            message_type=message_type,
            tokens_used=(
                response.usage.total_tokens if hasattr(response, "usage") else 0
            ),
            response_time=time.time() - start_time,
            model_version=model,
        )

        # Calcular tiempo y registrar respuesta
        response_time = time.time() - start_time
        assistant_response = (
            response.choices[0].message.content
            if hasattr(response, "choices")
            else response
        )

        # Registrar respuesta del asistente
        log_conversation(
            user_id=user_id,
            role="assistant",
            message=assistant_response,
            message_type=message_type,
            response_time=response_time,
            tokens_used=(
                response.usage.total_tokens if hasattr(response, "usage") else 0
            ),
            model_version=model,
            conversation_id=conversation_id,
        )

        # Actualizar historial local
        conversation_history[user_id].append(
            {"role": "assistant", "content": assistant_response}
        )

        return {"response": assistant_response}

    except Exception as e:
        logger.error(f"Error en chat: {str(e)}")
        if "conversation_id" in locals():
            error_time = time.time() - start_time
            log_conversation(
                user_id=user_id,
                role="system",
                message=str(e),
                message_type="error",
                tokens_used=(
                    response.usage.total_tokens
                    if "response" in locals() and hasattr(response, "usage")
                    else 0
                ),
                response_time=error_time,
                model_version=model,
                conversation_id=conversation_id,
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/whatsapp")
async def webhook_verify(
    hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None
):
    if hub_mode and hub_verify_token:
        if hub_mode == "subscribe" and hub_verify_token == "ASJROFDWDOERK":
            logger.info("WEBHOOK_VERIFIED")
            return int(hub_challenge)
        raise HTTPException(status_code=403, detail="Forbidden")
    raise HTTPException(status_code=400, detail="Invalid verification request")


@app.post("/whatsapp")
async def webhook(request: Request):
    try:
        data = await request.json()
        if not data:
            logger.error("No se recibieron datos")
            return "OK"

        logger.info("Procesando webhook")
        entry = data["entry"][0]
        if "changes" not in entry:
            return "OK"

        value = entry["changes"][0]["value"]

        if "messages" in value:
            message = value["messages"][0]
            # Verificar si el mensaje ya fue procesado
            message_id = message.get("id")
            if message_id in processed_messages:
                return "OK"

            processed_messages.add(message_id)
            number = message["from"]
            message_body = message["text"]["body"]

            # Obtener respuesta de OpenAI
            response = send_message_to_openai(message_body, number)

            # Enviar respuesta por WhatsApp
            body = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {"body": response},
            }
            whatsapp_service(body)

        return "OK"
    except Exception as e:
        logger.error(f"Error crítico en webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno")


@app.get("/test")
async def test():
    return "API funcionando!"


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8501))
    uvicorn.run(app, host="0.0.0.0", port=port)
