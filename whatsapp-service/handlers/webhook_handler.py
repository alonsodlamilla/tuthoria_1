import logging
from typing import Dict, Any, Optional
import requests
from loguru import logger
from collections import OrderedDict
from time import time
from config import get_settings

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self):
        self._processed_messages = set()  # Simple set to track processed messages
        self.settings = get_settings()
        self.token = self.settings.whatsapp_access_token
        self.api_url = self.settings.get_whatsapp_api_url()

    def is_message_processed(self, message_id: str) -> bool:
        return message_id in self._processed_messages

    def mark_message_processed(self, message_id: str, response: Optional[str] = None):
        self._processed_messages.add(message_id)

    def should_process_message(self, message: Dict) -> bool:
        if message.get("type") != "text":
            return False

        message_id = message.get("id")
        if not message_id:
            return False

        if message_id in self._processed_messages:
            logger.debug(f"Skipping message {message_id} - already handled")
            return False

        return True

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
            logger.error(f"Error sending WhatsApp message: {str(e)}", exc_info=True)
            return False

    def create_message_body(self, number: str, response: str) -> Dict[str, Any]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {"body": response},
        }

    def is_request_processed(self, request_id: str) -> bool:
        """Check if this request ID has been processed"""
        if not request_id:
            return False

        # Use the same cache mechanism
        return self.is_message_processed(f"req_{request_id}")
