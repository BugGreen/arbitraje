# telegram_alert.py
from src.telegram_bot.utils import load_telegram_credentials
from telegram.error import TelegramError
from telegram import Bot
import asyncio
import logging

# Configure logger for Telegram alerts
logger = logging.getLogger(__name__)


class TelegramAlert:
    def __init__(self):
        """
        Initializes the TelegramAlert instance with bot credentials.
        """
        self.bot_token, self.chat_id = load_telegram_credentials()
        self.bot = Bot(token=self.bot_token)

    async def send_message(self, message: str):
        """
        Sends a message to the defined Telegram chat asynchronously.

        :param message: The message to send.
        """
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logger.info(f"Alert sent to Telegram: {message}")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    async def send_error_alert(self, error_message: str):
        """
        Sends an error alert with the specific error message asynchronously.

        :param error_message: The error message to send.
        """
        message = f"⚠️ Error: {error_message}"
        await self.send_message(message)
