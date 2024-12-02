from typing import Optional, Dict, Any
import os
import logging
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationSummaryBufferMemory
from shared.templates import TEMPLATES
import httpx

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = OpenAI(
            api_key=api_key,
            http_client=httpx.Client(),
        )
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            api_key=api_key,
        )
        self.conversation_history = {}

    async def get_completion(self, message: str, user_id: str) -> str:
        """Simple GPT-4 completion"""
        try:
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = [
                    {"role": "system", "content": TEMPLATES["default"]}
                ]

            self.conversation_history[user_id].append(
                {"role": "user", "content": message}
            )

            response = self.client.chat.completions.create(
                model="gpt-4", messages=self.conversation_history[user_id]
            )

            assistant_response = response.choices[0].message.content
            self.conversation_history[user_id].append(
                {"role": "assistant", "content": assistant_response}
            )

            return assistant_response
        except Exception as e:
            logger.error(f"Error in get_completion: {str(e)}")
            raise

    async def get_langchain_response(
        self, user_prompt: str, current_state: str, context: Dict[str, Any]
    ) -> str:
        """LangChain-based response with state management"""
        try:
            template = TEMPLATES.get(current_state, TEMPLATES["INICIO"])

            if isinstance(template, str):
                template = template.format(
                    anio=context.get("anio") or "{anio}",
                    curso=context.get("curso") or "{curso}",
                    seccion=context.get("seccion") or "{seccion}",
                )

            prompt = PromptTemplate(
                input_variables=["current_state", "chat_history", "human_input"],
                template=template,
            )

            memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                memory_key="chat_history",
                input_key="human_input",
                max_token_limit=2000,
            )

            response = self.llm.generate(
                [
                    prompt.format(
                        current_state=current_state,
                        chat_history=memory.buffer,
                        human_input=user_prompt,
                    )
                ]
            )

            return response.generations[0][0].text
        except Exception as e:
            logger.error(f"Error in get_langchain_response: {str(e)}")
            raise