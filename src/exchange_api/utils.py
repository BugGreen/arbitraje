from dotenv import load_dotenv
import os
import logging
import requests
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


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


def handle_api_response(response: requests.Response) -> Dict[str, Any]:
    """
    Handles the API response for all exchanges.

    This function ensures that all exchanges return a consistent structure, and errors
    are logged and raised in a standardized way.

    :param response: The HTTP response from the exchange API.
    :return: A dictionary with the response data.
    :raises Exception: If the response status is not successful, logs and raises an error.
    """
    # Check for successful response with status codes 200, 201, 202 (or any other codes considered successful)
    if response.status_code in [200, 201, 202]:
        try:
            # Try to return JSON data
            return response.json()
        except ValueError:
            logger.error(f"Invalid JSON response: {response.text}")
            raise Exception(f"Invalid JSON response: {response.text}")
    else:
        # Log the error and raise an exception with a standard message
        logger.error(f"API Error {response.status_code}: {response.text}")
        raise Exception(f"API Error {response.status_code}: {response.text}")