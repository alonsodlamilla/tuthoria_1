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
from tiktoken import encoding_for_model

MAX_TOKENS = 6000  # GPT-4's context window is 8k, leave some room for response
SYSTEM_PROMPT_TOKENS = 200  # Approximate tokens for system prompt
BUFFER_TOKENS = 1000  # Leave room for the response


class ChatService:
    def __init__(self):
        logger.info("Initializing ChatService")
        try:
            # Initialize DB client (only for reading history)
            self.db_client = DBClient()
            logger.debug("DB client initialized successfully")

            # Initialize tokenizer
            self.tokenizer = encoding_for_model("gpt-4")
            logger.debug("Tokenizer initialized successfully")

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

    def _count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        return len(self.tokenizer.encode(text))

    def _trim_history_to_fit(
        self, history: List[BaseMessage], current_message: str
    ) -> List[BaseMessage]:
        """Trim history to fit within token limit"""
        current_tokens = self._count_tokens(current_message)
        available_tokens = (
            MAX_TOKENS - SYSTEM_PROMPT_TOKENS - current_tokens - BUFFER_TOKENS
        )

        if available_tokens <= 0:
            logger.warning("Message too long, no room for history")
            return []

        total_tokens = 0
        trimmed_history = []

        # Process messages from newest to oldest
        for msg in reversed(history):
            msg_tokens = self._count_tokens(msg.content)
            if total_tokens + msg_tokens > available_tokens:
                break
            total_tokens += msg_tokens
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

            # Trim history to fit token limit
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
            # Sort messages by timestamp to ensure chronological order
            sorted_history = sorted(
                history, key=lambda x: x.get("timestamp", datetime.min)
            )

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
