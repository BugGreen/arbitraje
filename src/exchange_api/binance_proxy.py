# exchange_api/binance_proxy.py
import json
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode
from typing import List, Dict, Optional
from src.exchange_api.base_exchange import BaseExchange
from src.exchange_api.utils import load_api_keys


class BinanceProxy(BaseExchange):
    """
    Proxy class for interacting with the Binance API.
    """

    BASE_URL = "https://api.binance.com"
    ENDPOINTS = {
        "ALL_COINS_INFO": "/sapi/v1/capital/config/getall",
        "DEPOSIT_ADDRESS": "/sapi/v1/capital/deposit/address",
        "WITHDRAW_REQUEST": "/sapi/v1/capital/withdraw/apply",
    }

    def __init__(self) -> None:
        """
        Initialize the BinanceProxy with API key and secret.
        """
        self.api_key, self.api_secret = load_api_keys("BINANCE")

    def _sign_request(self, params: Dict[str, str]) -> Dict[str, str]:
        """
        Sign the API request with HMAC SHA256.

        :param params: Dictionary of query parameters.
        :return: Dictionary of signed query parameters.
        """
        timestamp = int(time.time() * 1000)
        params["timestamp"] = str(timestamp)

        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        params["signature"] = signature
        return params

    def get_coin_info(self) -> List[Dict]:
        """
        Fetch information of all coins from Binance API.

        :return: List of dictionaries containing coin information.
        """
        url = f"{self.BASE_URL}{self.ENDPOINTS['ALL_COINS_INFO']}"
        headers = {"X-MBX-APIKEY": self.api_key}
        params = self._sign_request({})
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def supports_lightning_network(self, coin: str) -> bool:
        """
        Check if Binance supports the Lightning Network for a specific coin.

        :param coin: The symbol of the coin (e.g., 'BTC').
        :return: True if Lightning Network is supported and withdrawals are enabled, False otherwise.
        """
        coins_info = self.get_coin_info()
        for coin_info in coins_info:
            if coin_info.get("coin") == coin:
                # Uncomment to display the response
                # print(json.dumps(coin_info, indent=2))
                for network in coin_info.get("networkList", []):
                    if "lightning" in network.get("network", "").lower():
                        return network.get("withdrawEnable", False)
        return False

    def create_deposit_address(self, coin: str, network: Optional[str] = "LIGHTNING",
                               amount: Optional[float] = 0.00002) -> Dict:
        """
        Fetch a deposit address for a specific coin and network.

        :param coin: The symbol of the cryptocurrency (e.g., 'BTC').
        :param network: The network to use for the deposit (e.g., 'BTC', 'LIGHTNING'). If not provided, the default network is used.
        :param amount: The amount to deposit (only required for LIGHTNING network).
        :return: A dictionary containing the deposit address and related details.
        :raises Exception: If the request fails or the response contains an error.
        """
        network = network.upper()

        params = {
            "coin": coin,
            "timestamp": int(time.time() * 1000),
        }

        if network:
            params["network"] = network
        if amount and network and network == "LIGHTNING":
            params["amount"] = amount

        # Sign the request
        signed_params = self._sign_request(params)

        # Make the API request
        url = f"{self.BASE_URL}{self.ENDPOINTS['DEPOSIT_ADDRESS']}"
        headers = {"X-MBX-APIKEY": self.api_key}
        response = requests.get(url, headers=headers, params=signed_params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    def create_withdraw_request(self, coin: str, address: str, amount: float,
                                network: Optional[str] = "LIGHTNING", **kwargs) -> Dict:
        """
        Submit a withdrawal request to Binance.

        :param coin: The symbol of the cryptocurrency to withdraw (e.g., 'BTC').
        :param address: The destination address for the withdrawal.
        :param amount: The amount of cryptocurrency to withdraw.
        :param network: Optional, the network to use for withdrawal.
        :param kwargs: Additional optional parameters (e.g., withdrawOrderId, addressTag, transactionFeeFlag, name).
        :return: A dictionary containing the withdrawal request ID.
        :raises Exception: If the request fails or the response contains an error.
        """
        params = {
            "coin": coin,
            "address": address,
            "amount": amount,
            "timestamp": int(time.time() * 1000),
        }

        if network:
            params["network"] = network

        # Add additional optional parameters from kwargs
        optional_fields = ["withdrawOrderId", "addressTag", "transactionFeeFlag", "name", "walletType", "recvWindow"]
        for field in optional_fields:
            if field in kwargs:
                params[field] = kwargs[field]

        # Sign the request
        signed_params = self._sign_request(params)

        # Make the API request
        url = f"{self.BASE_URL}{self.ENDPOINTS['WITHDRAW_REQUEST']}"
        headers = {"X-MBX-APIKEY": self.api_key}
        response = requests.post(url, headers=headers, params=signed_params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")
