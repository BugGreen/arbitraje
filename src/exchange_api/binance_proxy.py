# exchange_api/binance_proxy.py
import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode
from typing import List, Dict
from src.exchange_api.base_exchange import BaseExchange
from src.exchange_api.utils import load_api_keys


class BinanceProxy(BaseExchange):
    """
    Proxy class for interacting with the Binance API.
    """

    BASE_URL = "https://api.binance.com"
    ENDPOINTS = {
        "ALL_COINS_INFO": "/sapi/v1/capital/config/getall",
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
                for network in coin_info.get("networkList", []):
                    if "lightning" in network.get("network", "").lower():
                        return network.get("withdrawEnable", False)
        return False
