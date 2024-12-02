import os
import logging
from typing import Dict, Any
import requests

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self):
        self.processed_messages = set()
        self.token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.api_url = os.getenv("WHATSAPP_API_URL")

    def send_whatsapp_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            }

            response = requests.post(self.api_url, headers=headers, json=body)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error en WhatsApp API: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error en whatsapp_service: {str(e)}")
            return None

    def is_message_processed(self, message_id: str) -> bool:
        return message_id in self.processed_messages

    def mark_message_processed(self, message_id: str):
        self.processed_messages.add(message_id)

    def create_message_body(self, number: str, response: str) -> Dict[str, Any]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {"body": response},
        }