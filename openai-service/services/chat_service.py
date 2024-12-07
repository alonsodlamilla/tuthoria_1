import os
from typing import Dict
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        # Initialize LangChain chat model
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize conversation memory
        self.memories = {}

    async def process_message(
        self,
        message: str,
        current_state: str,
        context: Dict[str, str]
    ) -> str:
        """Process a message using LangChain"""
        try:
            # Get or create memory for this conversation
            memory = self.memories.get(context.get('user_id'))
            if not memory:
                memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
                self.memories[context.get('user_id')] = memory
            
            # Create system message based on state and context
            system_template = self._create_system_message(current_state, context)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_template),
                ("human", "{input}"),
            ])
            
            # Create chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=memory,
                verbose=True
            )
            
            # Run chain
            response = await chain.arun(input=message)
            
            return response
            
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
