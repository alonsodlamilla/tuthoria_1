import logging
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import os
from typing import Optional, Dict, List
from services.chat_service import ChatService
from services.db_service import DBService
from datetime import datetime

from shared.templates.prompts import TEMPLATES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenAI Service", description="AI Chat Service with state management"
)
chat_service = ChatService()
db_service = DBService()


class ChatRequest(BaseModel):
    message: str
    user_id: str


class ChatResponse(BaseModel):
    response: str


class ConversationHistory(BaseModel):
    message: str
    response: str
    created_at: datetime


class SessionRequest(BaseModel):
    modalidad: str = Field(..., description="Modalidad educativa")
    nivel_educativo: str = Field(..., description="Nivel educativo")
    grado: str = Field(..., description="Grado")
    area_curricular: str = Field(..., description="Área curricular")
    competencia: str = Field(..., description="Competencia")
    capacidades: str = Field(..., description="Capacidades")
    tema: str = Field(..., description="Tema de la sesión")
    duracion: str = Field(..., description="Duración de la sesión")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint using GPT-4"""
    try:
        response = await chat_service.get_completion(request.message, request.user_id)
        await db_service.log_conversation(request.user_id, request.message, response)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/getresponsegpt", response_model=ChatResponse)
async def get_response_gpt(
    user_prompt: str = Query(..., description="User's input prompt"),
    user_id: str = Query(..., description="User's ID"),
):
    """Advanced chat endpoint with state management using LangChain"""
    try:
        # Get current state and context
        current_state, context = await db_service.get_user_state(user_id)

        # Get response using LangChain
        response = await chat_service.get_langchain_response(
            user_prompt, current_state, context
        )

        # Update state based on response
        new_context = context.copy()
        if current_state == "INICIO" and any(
            str(i) in user_prompt for i in range(1, 6)
        ):
            new_context["anio"] = f"{user_prompt}° año"
            await db_service.update_user_state(user_id, "SELECCION_CURSO", new_context)
        elif current_state == "SELECCION_CURSO" and any(
            str(i) in user_prompt for i in range(1, 5)
        ):
            cursos = {
                "1": "Matemática",
                "2": "Comunicación",
                "3": "Ciencias",
                "4": "Historia",
            }
            new_context["curso"] = cursos.get(user_prompt[0])
            await db_service.update_user_state(user_id, "SESION_FINAL", new_context)

        # Log conversation
        await db_service.log_conversation(user_id, user_prompt, response)

        return {"response": response}

    except Exception as e:
        logger.error(f"Error in get_response_gpt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{user_id}", response_model=List[ConversationHistory])
async def get_history(user_id: str, limit: int = Query(10, ge=1, le=100)):
    """Get conversation history for a user"""
    try:
        history = await db_service.get_conversation_history(user_id, limit)
        return history
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=ChatResponse)
async def generate_session(request: SessionRequest):
    """Generate a learning session based on educational context"""
    try:
        # Format the prompt with context
        formatted_prompt = TEMPLATES["session_template"].format(
            modalidad=request.modalidad,
            nivel=request.nivel_educativo,
            grado=request.grado,
            area=request.area_curricular,
            competencia=request.competencia,
            capacidades=request.capacidades,
            tema=request.tema,
            duracion=request.duracion,
        )

        # Get response using GPT-4
        response = await chat_service.get_completion(
            formatted_prompt, "session_generator"
        )

        # Log the session generation
        await db_service.log_conversation(
            user_id="session_generator",
            message=formatted_prompt,
            response=response,
        )

        return {"response": response}
    except Exception as e:
        logger.error(f"Error generating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8502))
    uvicorn.run(app, host="0.0.0.0", port=port)
