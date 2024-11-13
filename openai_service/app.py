from flask import Flask, request, jsonify
from openai import OpenAI
import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.templates.prompts import PROMPT_TEMPLATE
from utils.sheets_manager import SheetsManager

app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
sheets = SheetsManager()

# Diccionario para mantener el historial de conversaciones
conversation_history = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        start_time = time.time()
        data = request.json
        message = data.get('message')
        user_id = data.get('user_id')
        message_type = data.get('message_type', 'text')
        model = "gpt-4o"

        # Inicializar historial si no existe
        if user_id not in conversation_history:
            conversation_history[user_id] = [
                {"role": "system", "content": PROMPT_TEMPLATE}
            ]

        # Agregar mensaje del usuario al historial
        conversation_history[user_id].append(
            {"role": "user", "content": message}
        )

        # Obtener respuesta de OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=conversation_history[user_id]
        )

        # Registrar mensaje del usuario
        conversation_id = sheets.log_conversation(
            user_id=user_id,
            role="user",
            message=message,
            message_type=message_type,
            tokens_used=response.usage.total_tokens,
            response_time=time.time() - start_time,
            model_version=model
        )

        # Calcular tiempo y registrar respuesta
        response_time = time.time() - start_time
        assistant_response = response.choices[0].message.content
        
        # Registrar respuesta del asistente usando el mismo message_type
        sheets.log_conversation(
            user_id=user_id,
            role="assistant",
            message=assistant_response,
            message_type=message_type,  # Usar el mismo tipo que el usuario
            response_time=response_time,
            tokens_used=response.usage.total_tokens,
            model_version=model,
            conversation_id=conversation_id
        )

        # Actualizar historial local
        conversation_history[user_id].append(
            {"role": "assistant", "content": assistant_response}
        )

        return jsonify({"response": assistant_response})
    
    except Exception as e:
        print(f"Error en chat: {str(e)}")
        if 'conversation_id' in locals():
            error_time = time.time() - start_time
            sheets.log_conversation(
                user_id=user_id,
                role="system",
                message=str(e),
                message_type="error",
                tokens_used=response.usage.total_tokens if 'response' in locals() else 0,
                response_time=error_time,
                model_version=model,
                conversation_id=conversation_id
            )
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)