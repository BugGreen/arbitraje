from typing import Callable, Dict, Any, Tuple
from dotenv import load_dotenv
import requests
import logging
import time
import os

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(func: Callable, max_retries=4, base_delay=5, max_delay=240) -> Dict[str, Any]:
    """
    Retries a function call with exponential backoff.

    :param func: The function to call.
    :param max_retries: The maximum number of retries.
    :param base_delay: The base delay between retries (in seconds).
    :param max_delay: The maximum delay between retries (in seconds).
    :return: The result of the function call, or raises an exception after max_retries.
    """
    try_number = 0
    requests_error: str = 'no_error'
    for attempt in range(max_retries):
        try:
            return func()  # Call the function
        except requests.exceptions.RequestException as e:  # Handle network-related errors
            logger.error(f"RequestException occurred (Attempt {attempt + 1}/{max_retries}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                # Retry only for certain HTTP errors (502, 524, 429)
                if status_code in [502, 524, 429, 400, 401]:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.error(f"API Error {status_code} occurred (Attempt {attempt + 1}/{max_retries}). Retrying in {delay}s...")
                    time.sleep(delay)  # Wait before retrying
                    continue
            else:
                # Handle the case where no response was provided by the server
                logger.error(f"Remote connection closed without response (Attempt {attempt + 1}/{max_retries})")
                delay = min(base_delay * (3 ** attempt), max_delay)
                logger.error(f"Retrying in {delay}s...")
                time.sleep(delay)  # Wait before retrying
                continue
        except Exception as e:  # Handle other exceptions that do not have 'response' attribute
            logger.error(f"Unexpected error occurred (Attempt {attempt + 1}/{max_retries}): {e}")
            # After max retries, raise the exception
            raise Exception(f"{e}: Failed after {try_number} retries.")

    raise Exception(f"Failed after {try_number} retries.")


def handle_api_response(func: Callable, retry_attempts: int = 3, backoff_base_delay: int = 2) -> Dict[str, Any]:
    """
    Handles the API response for all exchanges with retry logic and standard error handling.

    :param func: The function to execute that performs the API call.
    :param retry_attempts: Number of retries for failed requests.
    :param backoff_base_delay: Base delay between retries.
    :return: A dictionary with the response data.
    :raises Exception: If the response status is not successful, logs and raises an error.
    """

    def api_call():
        try:
            response = func()  # The function that makes the request
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()  # If status is good, return JSON data
        except requests.exceptions.HTTPError as e:
            # Handle HTTPError exceptions (e.g., 4xx or 5xx responses)
            logger.error(f"HTTPError: {e.response.status_code} - {e.response.text}")
            raise e  # Re-raise the exception for retrying
        except requests.exceptions.RequestException as e:
            # Handle other request-related exceptions (timeouts, connection issues)
            logger.error(f"RequestException: {e}")
            raise e  # Re-raise for retrying

    # Retry logic with exponential backoff
    return retry_with_exponential_backoff(api_call)


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
