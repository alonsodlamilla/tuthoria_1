from flask import Flask, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.templates.prompts import PROMPT_TEMPLATE
from utils.sheets_manager import SheetsManager

# Cargar variables de entorno
load_dotenv()

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

def send_message_to_openai(message, number):
    """Envía el mensaje a OpenAI y obtiene la respuesta"""
    try:
        # Detectar tipo de mensaje
        message_type = "number" if message.strip().isdigit() else "text"
        
        # Hacer la llamada directamente a la función chat
        data = {
            "message": message,
            "user_id": number,
            "message_type": message_type
        }
        
        # Simular una request a la función chat
        with app.test_request_context('/chat', method='POST', json=data):
            response = chat()
            if isinstance(response, tuple):
                return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"
            return response.json['response']
            
    except Exception as e:
        print(f"Error en send_message_to_openai: {str(e)}")
        return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"

def whatsapp_service(body):
    """Envía mensaje a WhatsApp"""
    try:
        token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        api_url = os.getenv("WHATSAPP_API_URL")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=body
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en WhatsApp API: {response.text}")
            return None
    except Exception as e:
        print(f"Error en whatsapp_service: {str(e)}")
        return None

@app.route("/whatsapp", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode and token:
            if mode == "subscribe" and token == "ASJROFDWDOERK":
                print("WEBHOOK_VERIFIED")
                return str(challenge)
            else:
                return "Forbidden", 403
        return "Invalid verification request", 400
    
    elif request.method == "POST":
        try:
            data = request.get_json()
            if 'entry' not in data:
                return "OK", 200
                
            entry = data['entry'][0]
            if 'changes' not in entry:
                return "OK", 200
                
            value = entry['changes'][0]['value']
            
            if 'messages' in value:
                message = value['messages'][0]
                number = message['from']
                message_body = message['text']['body']
                
                # Obtener respuesta de OpenAI
                response = send_message_to_openai(message_body, number)
                
                # Enviar respuesta por WhatsApp
                body = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": number,
                    "type": "text",
                    "text": {"body": response}
                }
                whatsapp_service(body)
                    
            return "OK", 200
        except Exception as e:
            print(f"Error en webhook: {str(e)}")
            return str(e), 400

@app.route("/test", methods=["GET"])
def test():
    return "API funcionando!", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8501))
    app.run(host="0.0.0.0", port=port)