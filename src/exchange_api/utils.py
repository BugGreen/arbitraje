from dotenv import load_dotenv
import os
from typing import Tuple


def load_api_keys(exchange_name: str) -> Tuple[str, str]:
    """
    Load API keys for a specified exchange from environment variables.

    :param exchange_name: Name of the exchange (e.g., 'BINANCE', 'BUDA').
    :return: A tuple containing the API key and API secret.
    :raises ValueError: If API key or secret is not found.
    """
    exchange_name = exchange_name.upper()
    load_dotenv()  # Load environment variables from .env file

    api_key = os.getenv(f"{exchange_name}_API_KEY")
    api_secret = os.getenv(f"{exchange_name}_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(f"API key and secret for {exchange_name} must be set in the environment variables.")

    return api_key, api_secret
