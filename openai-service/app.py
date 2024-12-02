import logging
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import os
from typing import Optional, Dict
from services.chat_service import ChatService
from services.db_service import DBService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
chat_service = ChatService()
db_service = DBService()


class ChatRequest(BaseModel):
    message: str
    user_id: str


class ChatResponse(BaseModel):
    response: str


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


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8502))
    uvicorn.run(app, host="0.0.0.0", port=port)
