from openai import OpenAI
from flask import Flask, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from templates.prompts import PROMPT_TEMPLATE

load_dotenv()
app = Flask(__name__)
CORS(app)

# Inicializar el cliente de OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route("/getresponsegpt", methods=["GET"])
def get_response_gpt():
    user_prompt = request.args.get("user_prompt")
    user_id = request.args.get("user_id")
    
    print(f"Prompt recibido: {user_prompt}")
    print(f"User ID: {user_id}")
    
    try:
        print("Intentando llamar a OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": PROMPT_TEMPLATE},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        print(f"Respuesta de OpenAI: {response}")
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error detallado: {str(e)}")
        print(f"Tipo de error: {type(e)}")
        return f"Lo siento, hubo un error al procesar tu mensaje: {str(e)}"

if __name__ == "__main__":
    app.run(port=8000, debug=True) 