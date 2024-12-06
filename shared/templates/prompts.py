PROMPT_TEMPLATE = """
You are an AI assistant designed to help students and teachers. 
Be helpful, clear, and concise in your responses.
"""

TEMPLATES = {
    "default": PROMPT_TEMPLATE,
    "INICIO": """
        Bienvenido a TutorIA. Por favor, selecciona el año:
        1. Primer año
        2. Segundo año
        3. Tercer año
        4. Cuarto año
        5. Quinto año
    """,
    "SELECCION_CURSO": """
        Para {anio}, selecciona el curso:
        1. Matemática
        2. Comunicación
        3. Ciencias
        4. Historia
    """,
    "SESION_FINAL": """
        Para {curso} de {anio}, generaré una sesión de aprendizaje.
        Por favor, indícame el tema específico que deseas desarrollar.
    """,
    "session_template": """
    Genera una sesión de aprendizaje detallada con el siguiente contexto:
    
    Modalidad: {modalidad}
    Nivel Educativo: {nivel}
    Grado: {grado}
    Área Curricular: {area}
    Competencia: {competencia}
    Capacidades: {capacidades}
    Tema: {tema}
    Duración: {duracion}
    
    La sesión debe incluir:
    1. Propósito de aprendizaje
    2. Momentos de la sesión (inicio, desarrollo, cierre)
    3. Actividades específicas
    4. Materiales necesarios
    5. Evaluación
    
    Por favor, estructura la respuesta de manera clara y organizada.
    """,
}

__all__ = ["PROMPT_TEMPLATE", "TEMPLATES"]
