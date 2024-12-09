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
        # Use OrderedDict as an LRU cache with max size
        self._message_cache = OrderedDict()
        self._processing_cache = set()  # Track messages being processed
        self.MAX_CACHE_SIZE = 1000
        self.MESSAGE_TTL = 300  # 5 minutes TTL
        self.settings = get_settings()
        self.token = self.settings.whatsapp_access_token
        self.api_url = self.settings.get_whatsapp_api_url()

    def _clean_old_messages(self):
        """Remove messages older than TTL"""
        current_time = time()
        for msg_id, (timestamp, _) in list(self._message_cache.items()):
            if current_time - timestamp > self.MESSAGE_TTL:
                self._message_cache.pop(msg_id, None)
                if msg_id in self._processing_cache:
                    self._processing_cache.remove(msg_id)

    def is_message_processed(self, message_id: str) -> bool:
        """Check if message was already processed"""
        self._clean_old_messages()
        return message_id in self._message_cache

    def is_message_processing(self, message_id: str) -> bool:
        """Check if message is currently being processed"""
        return message_id in self._processing_cache

    def mark_message_processing(self, message_id: str):
        """Mark message as currently being processed"""
        self._processing_cache.add(message_id)

    def mark_message_processed(self, message_id: str, response: Optional[str] = None):
        """Mark message as processed with timestamp and response"""
        self._message_cache[message_id] = (time(), response)
        if len(self._message_cache) > self.MAX_CACHE_SIZE:
            # Remove oldest entry
            self._message_cache.popitem(last=False)
        # Remove from processing cache
        if message_id in self._processing_cache:
            self._processing_cache.remove(message_id)

    def should_process_message(self, message: Dict) -> bool:
        """Determine if a message should be processed"""
        # Skip if not a text message
        if message.get("type") != "text":
            return False

        message_id = message.get("id")
        if not message_id:
            return False

        # Skip if already processed or currently processing
        if self.is_message_processed(message_id) or self.is_message_processing(
            message_id
        ):
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
