from flask import Flask, request, make_response
import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Obtener la ruta a la raíz del proyecto (un nivel arriba de whatsapp-service)
root_dir = Path(__file__).parent.parent
env_path = os.path.join(root_dir, '.env')

# Cargar variables de entorno especificando la ruta
load_dotenv(env_path)

# Agregar logs de debug
print(f"Ruta del .env: {env_path}")
print(f"El archivo .env existe: {os.path.exists(env_path)}")

# Resto de las variables
ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL')
WHATSAPP_NUMBER_ID = os.getenv('WHATSAPP_NUMBER_ID')
OPENAI_SERVICE_URL = os.getenv('OPENAI_SERVICE_URL')

# Logs de verificación
print("\nVariables de entorno cargadas:")
print(f"OPENAI_SERVICE_URL: {OPENAI_SERVICE_URL}")
print(f"WHATSAPP_API_URL: {WHATSAPP_API_URL}")
print(f"WHATSAPP_NUMBER_ID: {WHATSAPP_NUMBER_ID}")
print(f"VERIFY_TOKEN: {VERIFY_TOKEN}")

app = Flask(__name__)

@app.route("/saludar", methods=["GET"])
def saludar():
    response = make_response("Hola")
    # Agregar headers específicos para evitar la intercepción de ngrok
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

@app.route("/whatsapp", methods=["GET"])
def verify_token():
    try:
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        print("=== VERIFICACIÓN DE TOKEN ===")
        print(f"Token recibido: {token}")
        print(f"Challenge recibido: {challenge}")
        print(f"VERIFY_TOKEN configurado: {VERIFY_TOKEN}")
        
        if token == VERIFY_TOKEN:
            response = make_response(challenge)
            response.headers['Content-Type'] = 'text/plain'
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Connection'] = 'keep-alive'
            response.headers['ngrok-skip-browser-warning'] = 'true'
            return response
        else:
            return "Error en la verificación del token.", 400
            
    except Exception as e:
        print(f"Error en verify_token: {str(e)}")
        return str(e), 400

@app.route("/whatsapp", methods=["POST"])
def webhook():
    try:
        print("====== NUEVO MENSAJE RECIBIDO ======")
        print(f"Headers: {request.headers}")
        data = request.get_json()
        print(f"Data completa: {json.dumps(data, indent=2)}")
        
        if 'entry' not in data:
            print("No hay entry en data")
            return "OK", 200
            
        entry = data['entry'][0]
        if 'changes' not in entry:
            print("No hay changes en entry")
            return "OK", 200
            
        value = entry['changes'][0]['value']
        print(f"Value recibido: {value}")
        
        if 'messages' in value:
            message = value['messages'][0]
            number = message['from']
            message_body = message['text']['body']
            print(f"Mensaje del usuario: {message_body}")
            
            body = enviar_mensaje(message_body, number)
            whatsapp_service(body)
        elif 'statuses' in value:
            print("Recibida actualización de estado")
            
        return "OK", 200
    except Exception as e:
        print(f"Error detallado: {str(e)}")
        return str(e), 400

def whatsapp_service(body):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        
        response = requests.post(WHATSAPP_API_URL, data=json.dumps(body), headers=headers)
        
        print(f"Estado de la respuesta: {response.text}")
        return response.status_code == 200
        
    except Exception as e:
        print(e)
        return False
    
def enviar_mensaje(text, numero):
    print(f"OPENAI_SERVICE_URL en enviar_mensaje: {OPENAI_SERVICE_URL}")
    # Codificar el texto para la URL
    text_encoded = requests.utils.quote(text)
    url = f"{OPENAI_SERVICE_URL}/getresponsegpt?user_prompt={text_encoded}&user_id={numero}"
    print(f"URL completa: {url}")
    try:
        response_gpt = requests.get(url)
        print(f"Status code: {response_gpt.status_code}")
        print(f"Respuesta: {response_gpt.text}")
        response_text = response_gpt.text
    except Exception as e:
        print(f"Error al llamar a OpenAI service: {str(e)}")
        response_text = "Lo siento, hubo un error al procesar tu mensaje."
    
    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero,
        "type": "text",
        "text": {"body": response_text}
    }
    return body

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8501, debug=True)
