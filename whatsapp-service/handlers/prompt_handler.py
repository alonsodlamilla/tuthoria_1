import sys
import os
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.templates.prompts import PROMPT_TEMPLATE

class PromptHandler:
    def __init__(self):
        self.base_prompt = PROMPT_TEMPLATE
        self.openai_service_url = os.getenv('OPENAI_SERVICE_URL')

    def generate_session(self, context):
        """Genera la sesión de aprendizaje usando GPT"""
        try:
            # Formatear el prompt con el contexto
            formatted_prompt = self.base_prompt.format(
                modalidad=context.get('MODALIDAD', ''),
                nivel=context.get('NIVEL_EDUCATIVO', ''),
                grado=context.get('GRADO', ''),
                area=context.get('AREA_CURRICULAR', ''),
                competencia=context.get('COMPETENCIA', ''),
                capacidades=context.get('CAPACIDADES', ''),
                tema=context.get('TEMA', ''),
                duracion=context.get('DURACION', '')
            )

            # Llamar al servicio de OpenAI
            response = self.call_openai_service(formatted_prompt)
            return response

        except Exception as e:
            print(f"Error en generate_session: {str(e)}")
            raise

    def call_openai_service(self, prompt):
        """Llama al servicio de OpenAI"""
        try:
            response = requests.post(
                f"{self.openai_service_url}/generate",
                json={"prompt": prompt}
            )
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Error del servicio OpenAI: {response.text}")
        except Exception as e:
            print(f"Error llamando a OpenAI service: {str(e)}")
            raise 