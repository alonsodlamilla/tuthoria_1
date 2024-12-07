import os
from typing import Dict, List
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from db_service.client import DBClient
from shared.templates.prompts import SYSTEM_PROMPT

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
        self.db_client = DBClient()
        
        # Initialize prompt template with external system prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

    async def process_message(
        self,
        message: str,
        context: Dict[str, str]
    ) -> str:
        """Process a message using LangChain"""
        try:
            # Get conversation history from DB service
            history = await self.db_client.get_conversation_history(context.get('user_id'))
            
            # Process with LangChain
            response = await self._process_with_langchain(message, history, context)
            
            # Let DB service handle storage
            await self.db_client.log_conversation(
                context.get('user_id'),
                message,
                response
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            raise

    async def _process_with_langchain(
        self,
        message: str,
        history: List[BaseMessage],
        context: Dict[str, str]
    ) -> str:
        """Process a message with conversation history using LangChain"""
        try:
            # Create chain
            chain = LLMChain(
                llm=self.llm,
                prompt=self.prompt,
                verbose=True
            )
            
            # Format history into messages
            chat_history = []
            for msg in history:
                if isinstance(msg, dict):  # Handle history from DB
                    if msg.get("role") == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))
                else:  # Handle BaseMessage objects
                    chat_history.append(msg)

            # Run chain
            response = await chain.ainvoke({
                "chat_history": chat_history,
                "input": message
            })
            
            return response["text"]
            
        except Exception as e:
            logger.error(f"Error in _process_with_langchain: {str(e)}")
            raise
