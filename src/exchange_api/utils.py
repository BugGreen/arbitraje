from typing import Callable, Dict, Any, Tuple
from dotenv import load_dotenv
import requests
import logging
import time
import os

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(func: Callable, max_retries=3, base_delay=2, max_delay=10) -> Dict[str, Any]:
    """
    Retries a function call with exponential backoff.

    :param func: The function to call.
    :param max_retries: The maximum number of retries.
    :param base_delay: The base delay between retries (in seconds).
    :param max_delay: The maximum delay between retries (in seconds).
    :return: The result of the function call, or raises an exception after max_retries.
    """
    try_number = 0
    for attempt in range(max_retries):
        try:
            return func()  # Call the function
        except requests.exceptions.RequestException as e:  # Handle general network issues
            logger.error(f"RequestException occurred (Attempt {attempt + 1}/{max_retries}): {e}")
            # Retry only if we catch a specific error (502 or 524)
            if hasattr(e, 'response') and e.response:
                status_code = e.response.status_code
                if status_code in [502, 524]:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.error(
                        f"API Error {status_code} occurred (Attempt {attempt + 1}/{max_retries}). Retrying in {delay}s...")
                    time.sleep(delay)  # Wait before retrying
                    try_number = attempt + 1
                    continue

        except Exception as e:  # Catch other exceptions
            logger.error(f"Unexpected error occurred (Attempt {attempt + 1}/{max_retries}): {e}")
            # After max retries, raise exception
            raise Exception(f"{e}: Failed after {try_number} retries.")


def handle_api_response(response: requests.Response, retry_attempts: int = 3, backoff_base_delay: int = 2) \
        -> Dict[str, Any]:
    """
    Handles the API response for all exchanges with retry logic and standard error handling.

    :param response: The HTTP response from the exchange API.
    :param retry_attempts: Number of retries for failed requests.
    :param backoff_base_delay: Base delay between retries.
    :return: A dictionary with the response data.
    :raises Exception: If the response status is not successful, logs and raises an error.
    """
    def api_call():
        # Check for successful response with status codes 200, 201, or 202
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

    # Retry logic with exponential backoff
    return retry_with_exponential_backoff(api_call, max_retries=retry_attempts, base_delay=backoff_base_delay)


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
