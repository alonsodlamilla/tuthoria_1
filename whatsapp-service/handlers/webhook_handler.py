import logging
from typing import Dict, Any
import requests
from loguru import logger
from collections import OrderedDict
from functools import lru_cache
from time import time
from config import get_settings

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self):
        # Use OrderedDict as an LRU cache with max size
        self.processed_messages = OrderedDict()
        self.MAX_CACHE_SIZE = 1000
        self.MESSAGE_TTL = 300  # 5 minutes TTL
        self.settings = get_settings()
        self.token = self.settings.whatsapp_access_token
        self.api_url = self.settings.get_whatsapp_api_url()

    def is_message_processed(self, message_id: str) -> bool:
        """Check if message was already processed and clean old entries"""
        self._clean_old_messages()
        return message_id in self.processed_messages

    def mark_message_processed(self, message_id: str):
        """Mark message as processed with timestamp"""
        self.processed_messages[message_id] = time()
        if len(self.processed_messages) > self.MAX_CACHE_SIZE:
            # Remove oldest entry
            self.processed_messages.popitem(last=False)

    def _clean_old_messages(self):
        """Remove messages older than TTL"""
        current_time = time()
        for msg_id, timestamp in list(self.processed_messages.items()):
            if current_time - timestamp > self.MESSAGE_TTL:
                self.processed_messages.pop(msg_id, None)

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
