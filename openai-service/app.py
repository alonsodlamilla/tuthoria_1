from fastapi import FastAPI, HTTPException, logger
from pydantic import BaseModel
from openai import OpenAI
import os
from typing import Optional, Dict, List
from shared.templates import TEMPLATES
from utils.sheets_manager import SheetsManager

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
sheets = SheetsManager()

# Diccionario para mantener el historial de conversaciones
conversation_history = {}


class ChatRequest(BaseModel):
    message: str
    user_id: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        message = request.message
        user_id = request.user_id

        if user_id not in conversation_history:
            conversation_history[user_id] = [
                {"role": "system", "content": TEMPLATES["default"]}
            ]

        conversation_history[user_id].append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-4", messages=conversation_history[user_id]
        )

        assistant_response = response.choices[0].message.content

        conversation_history[user_id].append(
            {"role": "assistant", "content": assistant_response}
        )

        return {"response": assistant_response}
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8502))
    uvicorn.run(app, host="0.0.0.0", port=port)
