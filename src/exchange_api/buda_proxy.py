# exchange_api/buda_proxy.py
import base64
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode
from typing import List, Dict, Optional
from src.exchange_api.base_exchange import BaseExchange
from src.exchange_api.utils import load_api_keys
import json


class BudaProxy(BaseExchange):
    """
    Proxy class for interacting with the BUDA API.
    """

    def __init__(self) -> None:
        """
        Initialize the BudaProxy with API key and secret.
        """
        self.api_key, self.api_secret = load_api_keys("BUDA")

    BASE_URL = "https://www.buda.com"
    ENDPOINTS = {
        "LIGHTNING_INVOICE": "/api/v2/lightning_network_invoices",
        "LIGHTNING_WITHDRAWAL": "/api/v2/reserves/ln-btc/withdrawals"
    }

    def _sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """
        Sign a request to authenticate with the Buda API.

        :param method: HTTP method (GET, POST, PUT).
        :param path: API path (including query string if applicable).
        :param body: Request body as a string (default is empty).
        :return: Headers containing API key, nonce, and signature for authentication.
        """
        # Generate nonce (current timestamp in microseconds)
        nonce = str(int(time.time() * 1e6))

        # Prepare string for signing
        if body:
            # Convert body to JSON string and encode it in Base64
            base64_encoded_body = base64.b64encode(json.dumps(body).encode()).decode()
        else:
            base64_encoded_body = ""

        string_to_sign = f"{method} {path} {base64_encoded_body} {nonce}"

        # Generate HMAC-SHA384 signature
        signature = hmac.new(
            key=self.api_secret.encode(),
            msg=string_to_sign.encode(),
            digestmod=hashlib.sha384
        ).hexdigest()

        # Return headers
        return {
            "X-SBTC-APIKEY": self.api_key,
            "X-SBTC-NONCE": nonce,
            "X-SBTC-SIGNATURE": signature,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://www.buda.com",
            "Origin": "https://www.buda.com"
        }

    def create_deposit_address(self, coin: str = "BTC", network: Optional[str] = "lightning",
                               amount_satoshis: int = 0, memo: Optional[str] = None,
                               expiry_seconds: Optional[int] = 0) -> Dict:
        """
        Create a Lightning Network deposit address (invoice) for BTC.

        :param coin: The cryptocurrency symbol (e.g., 'BTC'). Must be 'BTC' for Lightning Network.
        :param network: The network for the deposit. If provided, must be 'lightning'.
        :param amount_satoshis: The amount of the invoice in satoshis.
        :param memo: Optional brief description for the invoice.
        :param expiry_seconds: Optional expiry time for the invoice in seconds.
        :return: A dictionary containing the encoded payment request.
        :raises Exception: If the request fails or the response contains an error.
        """
        if coin != "BTC":
            raise ValueError("Lightning Network invoices are only supported for BTC.")
        if network and network.lower() != "lightning":
            raise ValueError("This method only supports the Lightning Network.")

        # Define the endpoint path
        endpoint_path = self.ENDPOINTS["LIGHTNING_INVOICE"]
        url = f"{self.BASE_URL}{endpoint_path}"

        # Build the payload
        payload = {
            "amount_satoshis": amount_satoshis,
            "currency": "BTC"
        }
        if memo:
            payload["memo"] = memo
        if expiry_seconds:
            payload["expiry_seconds"] = expiry_seconds

        # Authenticate the request
        headers = self._sign_request(method="POST", path=endpoint_path, body=payload if payload else "")

        # Make the API call
        response = requests.post(url, headers=headers, json=payload)

        # Handle the response
        if response.status_code in [200, 201]:
            return response.json().get("invoice", {})
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def get_coin_info(self) -> List[Dict]:
        pass

    def supports_lightning_network(self, coin: str) -> bool:
        pass

    def create_withdraw_request(self, coin: str, address: str,
                                amount: float, simulate: bool = False) -> Dict:
        """
        Submit a withdrawal request for a Lightning Network payment.

        :param coin: The cryptocurrency symbol (e.g., 'BTC'). Must be 'BTC' for Lightning Network.
        :param address: The Lightning Network invoice received from the receiver.
        :param amount: The withdrawal amount in BTC.
        :param simulate: Optional flag to simulate the payment request without executing it.
        :return: A dictionary containing the details of the withdrawal request.
        :raises ValueError: If the coin is not 'BTC'.
        :raises Exception: If the request fails or the response contains an error.
        """
        if coin.upper() != "BTC":
            raise ValueError("This method only supports Lightning Network withdrawals for BTC.")

        # Define the endpoint path
        endpoint_path = self.ENDPOINTS["LIGHTNING_WITHDRAWAL"]
        url = f"{self.BASE_URL}{endpoint_path}"

        payload = {
            "amount": amount,
            "withdrawal_data": {
                "payment_request": address
            }
        }

        # Authenticate the request
        headers = self._sign_request(method="POST", path=endpoint_path, body=payload)

        # Make the API call
        response = requests.post(url, headers=headers, json=payload)

        # Handle the response
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def new_order(self, symbol: str, side: str, order_type: str,
                  timestamp: Optional[int],
                  quantity: Optional[float] = None,
                  price: Optional[float] = None,
                  time_in_force: Optional[str] = None,
                  stop_price: Optional[float] = None,
                  iceberg_qty: Optional[float] = None,
                  quote_order_qty: Optional[float] = None,
                  new_client_order_id: Optional[str] = None,
                  strategy_id: Optional[int] = None,
                  strategy_type: Optional[int] = None,
                  trailing_delta: Optional[int] = None,
                  new_order_resp_type: Optional[str] = None,
                  self_trade_prevention_mode: Optional[str] = None,
                  recv_window: Optional[int] = None) -> Dict:
        # ToDo: Complete this
        pass
