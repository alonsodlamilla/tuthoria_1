import logging
from typing import Dict, Any
import requests
from config import get_settings

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self):
        self.processed_messages = set()
        self.settings = get_settings()
        self.token = self.settings.whatsapp_access_token
        self.api_url = self.settings.get_whatsapp_api_url()

    def send_whatsapp_message(self, body: Dict[str, Any]) -> bool:
        """Send message to WhatsApp API"""
        try:
            logger.info("Sending WhatsApp message to: %s", body.get("to"))
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            }

            response = requests.post(self.api_url, headers=headers, json=body)
            response.raise_for_status()

            logger.info("WhatsApp message sent successfully to: %s", body.get("to"))
            return True
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False

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
