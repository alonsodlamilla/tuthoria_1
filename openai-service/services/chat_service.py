import os
import openai
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"

    async def process_message(
        self,
        message: str,
        current_state: str,
        context: Dict[str, str]
    ) -> str:
        """Process a message using OpenAI's GPT-4"""
        try:
            # Create system message based on state and context
            system_message = self._create_system_message(current_state, context)
            
            # Create the messages array for the chat
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ]
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            raise

    def _create_system_message(self, current_state: str, context: Dict[str, str]) -> str:
        """Create a system message based on the current state and context"""
        base_message = "You are a helpful AI assistant."
        
        if current_state == "INICIO":
            return f"{base_message} You are helping a student choose their academic year."
        elif current_state == "SELECCION_CURSO":
            year = context.get("anio", "unknown year")
            return f"{base_message} You are helping a {year} student choose their course."
        elif current_state == "SESION_FINAL":
            year = context.get("anio", "unknown year")
            course = context.get("curso", "unknown course")
            return f"{base_message} You are helping a {year} student with their {course} course."
        
        return base_message
