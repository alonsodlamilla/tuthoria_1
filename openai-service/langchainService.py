from flask import Flask, request, jsonify
import os
import psycopg2
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory
from shared.templates import TEMPLATES

app = Flask(__name__)

# Configuración de base de datos
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'docente_bot')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASSWORD', 'secret')

# Configuración OpenAI
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.route("/getresponsegpt", methods=["GET"])
def get_response_gpt():
    user_prompt = request.args.get("user_prompt")
    user_id = request.args.get("user_id")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obtener estado actual y datos del usuario
    cur.execute("""
        SELECT current_state, anio, curso, seccion 
        FROM user_states 
        WHERE user_id = %s
    """, (user_id,))
    user_data = cur.fetchone()
    
    if not user_data:
        # Nuevo usuario - crear registro
        cur.execute(
            "INSERT INTO user_states (user_id) VALUES (%s) RETURNING current_state",
            (user_id,)
        )
        conn.commit()
        current_state = "INICIO"
    else:
        current_state, anio, curso, seccion = user_data

    # Obtener template según estado
    template = TEMPLATES.get(current_state, TEMPLATES["INICIO"])
    
    if isinstance(template, str):
        template = template.format(
            anio=anio or "{anio}",
            curso=curso or "{curso}",
            seccion=seccion or "{seccion}"
        )

    # Configurar prompt
    prompt = PromptTemplate(
        input_variables=["current_state", "chat_history", "human_input"],
        template=template
    )
    
    # Inicializar OpenAI y memoria (se mantiene igual)
    llm = OpenAI(model_name="gpt-4o", api_key=OPENAI_API_KEY)
    llm = OpenAI(model_name="gpt-4o", api_key=OPENAI_API_KEY)
    memory = ConversationSummaryBufferMemory(
        llm=llm,
        memory_key="chat_history",
        input_key="human_input",
        max_token_limit=2000
    )
    
    # Generar respuesta
    response = llm.generate([prompt.format(
        current_state=current_state,
        chat_history=memory.buffer,
        human_input=user_prompt
    )])

    # Actualizar estado según la respuesta
    if current_state == "INICIO" and any(str(i) in user_prompt for i in range(1, 6)):
        anio = f"{user_prompt}° año"
        cur.execute(
            "UPDATE user_states SET current_state = 'SELECCION_CURSO', anio = %s WHERE user_id = %s",
            (anio, user_id)
        )
    elif current_state == "SELECCION_CURSO" and any(str(i) in user_prompt for i in range(1, 5)):
        cursos = {
            "1": "Matemática",
            "2": "Comunicación",
            "3": "Ciencias",
            "4": "Historia"
        }
        curso = cursos.get(user_prompt[0])
        cur.execute(
            "UPDATE user_states SET current_state = 'SESION_FINAL', curso = %s WHERE user_id = %s",
            (curso, user_id)
        )
    
    # Guardar en historial
    cur.execute(
        "INSERT INTO conversation_history (user_id, message, response) VALUES (%s, %s, %s)",
        (user_id, user_prompt, response.generations[0][0].text)
    )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return response.generations[0][0].text

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8502))
    app.run(host='0.0.0.0', port=port, debug=False)
