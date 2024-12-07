import os
from typing import Dict, List
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from shared.templates.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize prompt template with external system prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

    async def process_message(
        self,
        message: str,
        user_id: str,
        history: List[Dict]
    ) -> str:
        """Process a message using LangChain"""
        try:
            # Format history into messages
            chat_history = self._format_history(history)
            
            # Create chain
            chain = LLMChain(
                llm=self.llm,
                prompt=self.prompt,
                verbose=True
            )
            
            # Run chain
            response = await chain.ainvoke({
                "chat_history": chat_history,
                "input": message
            })
            
            return response["text"]
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            raise

    def _format_history(self, history: List[Dict]) -> List[BaseMessage]:
        """Format DB history into LangChain messages"""
        chat_history = []
        for msg in history:
            if msg.get("message"):
                chat_history.append(HumanMessage(content=msg["message"]))
            if msg.get("response"):
                chat_history.append(AIMessage(content=msg["response"]))
        return chat_history
