from typing import Dict, List
import os
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from shared.templates.prompts import SYSTEM_PROMPT
from services.db_client import DBClient
from datetime import datetime

MAX_CHARS = 12000  # Approximate character limit for context window
SYSTEM_PROMPT_CHARS = 400  # Approximate chars for system prompt
BUFFER_CHARS = 2000  # Leave room for the response


class ChatService:
    def __init__(self):
        logger.info("Initializing ChatService")
        try:
            # Initialize DB client (only for reading history)
            self.db_client = DBClient()
            logger.debug("DB client initialized successfully")

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

    def _count_chars(self, text: str) -> int:
        """Count characters in a text string"""
        return len(text)

    def _trim_history_to_fit(
        self, history: List[BaseMessage], current_message: str
    ) -> List[BaseMessage]:
        """Trim history to fit within character limit"""
        current_chars = self._count_chars(current_message)
        available_chars = MAX_CHARS - SYSTEM_PROMPT_CHARS - current_chars - BUFFER_CHARS

        if available_chars <= 0:
            logger.warning("Message too long, no room for history")
            return []

        total_chars = 0
        trimmed_history = []

        # Process messages from newest to oldest
        for msg in reversed(history):
            msg_chars = self._count_chars(msg.content)
            if total_chars + msg_chars > available_chars:
                break
            total_chars += msg_chars
            trimmed_history.insert(0, msg)  # Insert at beginning to maintain order

        logger.info(
            f"Trimmed history from {len(history)} to {len(trimmed_history)} messages"
        )
        return trimmed_history

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

            # Trim history to fit character limit
            trimmed_history = self._trim_history_to_fit(chat_history, message)
            logger.debug(f"Trimmed history length: {len(trimmed_history)}")

            # Create messages for the prompt
            messages = self.prompt.format_messages(
                chat_history=trimmed_history, input=message
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
            raise

    def _format_history(self, history: List[Dict]) -> List[BaseMessage]:
        """Format DB history into LangChain messages"""
        logger.debug(f"Formatting history of length: {len(history)}")
        try:
            chat_history = []
            # Filter out messages without required fields first
            valid_history = []
            for msg in history:
                if not isinstance(msg, dict):
                    logger.warning(f"Skipping non-dict message: {msg}")
                    continue
                if "timestamp" not in msg:
                    logger.warning(f"Skipping message without timestamp: {msg}")
                    continue
                valid_history.append(msg)

            # Sort messages by timestamp to ensure chronological order
            sorted_history = sorted(valid_history, key=lambda x: x["timestamp"])

            for msg in sorted_history:
                if not msg.get("content"):
                    logger.warning("Skipping message without content")
                    continue

                if msg.get("sender") == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                    logger.debug(f"Added human message: {msg['content'][:50]}...")
                elif msg.get("sender") == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
                    logger.debug(f"Added AI message: {msg['content'][:50]}...")
                else:
                    logger.warning(f"Unknown sender type: {msg.get('sender')}")

            logger.info(
                f"Successfully formatted {len(chat_history)} messages from {len(history)} total"
            )
            return chat_history

        except Exception as e:
            logger.error(f"Error formatting history: {str(e)}", exc_info=True)
            logger.error(f"Raw history: {history}")
            raise

    async def close(self):
        """Close the service and its clients"""
        logger.info("Closing ChatService")
        await self.db_client.close()
