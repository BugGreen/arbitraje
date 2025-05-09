from dotenv import load_dotenv
import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def load_telegram_credentials() -> Tuple[str, str]:
    """
    Load API credentials for the telegram bot.

    :return: A tuple containing the bot TOKEN and CHAT ID.
    :raises ValueError: If API key or secret is not found.
    """

    load_dotenv()  # Load environment variables from .env file

    token = os.getenv(f"TELEGRAM_TOKEN")
    chat_id = os.getenv(f"TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError(f"API Token and Chat-ID for telegram must be set in the environment variables.")

    return token, chat_id
