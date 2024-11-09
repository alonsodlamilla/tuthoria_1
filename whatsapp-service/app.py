from flask import Flask, request
import os
from dotenv import load_dotenv
import requests

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

def send_message_to_openai(message, number):
    """Envía el mensaje a OpenAI y obtiene la respuesta"""
    try:
        response = requests.post(
            f"{os.getenv('OPENAI_SERVICE_URL')}/chat",
            json={
                "message": message,
                "user_id": number  # Enviamos el número como ID de usuario
            }
        )
        if response.status_code == 200:
            return response.json()['response']
        else:
            raise Exception(f"Error del servicio OpenAI: {response.text}")
    except Exception as e:
        print(f"Error llamando a OpenAI service: {str(e)}")
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501)