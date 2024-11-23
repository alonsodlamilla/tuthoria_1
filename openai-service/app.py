from flask import Flask, request, jsonify
from openai import OpenAI
import os
import sys
import time
from shared.templates import TEMPLATES
from utils.sheets_manager import SheetsManager

app = Flask(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
sheets = SheetsManager()

# Diccionario para mantener el historial de conversaciones
conversation_history = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message')
        user_id = data.get('user_id')
        
        if user_id not in conversation_history:
            conversation_history[user_id] = [
                {"role": "system", "content": TEMPLATES["default"]}
            ]
        
        conversation_history[user_id].append(
            {"role": "user", "content": message}
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=conversation_history[user_id]
        )

        assistant_response = response.choices[0].message.content
        
        conversation_history[user_id].append(
            {"role": "assistant", "content": assistant_response}
        )

        return jsonify({"response": assistant_response})
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8502))
    app.run(host='0.0.0.0', port=port)