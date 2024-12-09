from typing import Dict, List
import os
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from shared.templates.prompts import SYSTEM_PROMPT


class ChatService:
    def __init__(self):
        logger.info("Initializing ChatService")
        try:
            # Initialize the ChatOpenAI model with proper configuration
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=1000,
                api_key=os.getenv("OPENAI_API_KEY"),
                streaming=True,
            )
            logger.debug("ChatOpenAI model initialized successfully")

            # Initialize prompt template with external system prompt
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                ]
            )
            logger.debug("Prompt template initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing ChatService: {str(e)}")
            raise

    async def process_message(
        self, message: str, user_id: str, history: List[Dict]
    ) -> str:
        """Process a message using LangChain"""
        logger.info(f"Processing message for user {user_id}")
        logger.debug(f"Message content: {message}")
        logger.debug(f"History length: {len(history)}")

        try:
            # Format history into messages
            chat_history = self._format_history(history)
            logger.debug(f"Formatted chat history length: {len(chat_history)}")

            # Create messages for the prompt
            messages = self.prompt.format_messages(
                chat_history=chat_history, input=message
            )
            logger.debug(f"Formatted messages for LLM")

            # Run chain
            logger.info("Invoking LLM")
            response = await self.llm.ainvoke(messages)
            logger.debug(f"Raw LLM response: {response}")

            logger.info(f"Successfully processed message for user {user_id}")
            return response.content

        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            logger.error(f"Input message: {message}")
            logger.error(f"User ID: {user_id}")
            logger.error(f"History length: {len(history)}")
            raise

    def _format_history(self, history: List[Dict]) -> List[BaseMessage]:
        """Format DB history into LangChain messages"""
        logger.debug(f"Formatting history of length: {len(history)}")
        try:
            chat_history = []
            for msg in history:
                if msg.get("message"):
                    chat_history.append(HumanMessage(content=msg["message"]))
                    logger.trace(f"Added human message: {msg['message'][:50]}...")
                if msg.get("response"):
                    chat_history.append(AIMessage(content=msg["response"]))
                    logger.trace(f"Added AI message: {msg['response'][:50]}...")

            logger.debug(f"Successfully formatted {len(chat_history)} messages")
            return chat_history

        except Exception as e:
            logger.error(f"Error formatting history: {str(e)}", exc_info=True)
            logger.error(f"Raw history: {history}")
            raise
