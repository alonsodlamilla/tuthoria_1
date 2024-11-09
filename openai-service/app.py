from flask import Flask, request, jsonify
from openai import OpenAI
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.templates.prompts import PROMPT_TEMPLATE

app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Diccionario para mantener el historial de conversaciones
conversation_history = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message')
        user_id = data.get('user_id')  # Necesitamos el ID del usuario

        # Inicializar historial si no existe
        if user_id not in conversation_history:
            conversation_history[user_id] = [
                {"role": "system", "content": PROMPT_TEMPLATE}
            ]

        # Agregar mensaje del usuario al historial
        conversation_history[user_id].append(
            {"role": "user", "content": message}
        )

        # Obtener respuesta de OpenAI con todo el historial
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history[user_id]
        )

        # Agregar respuesta al historial
        assistant_response = response.choices[0].message.content
        conversation_history[user_id].append(
            {"role": "assistant", "content": assistant_response}
        )

        return jsonify({"response": assistant_response})
    except Exception as e:
        print(f"Error en chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 