# exchange_api/binance_proxy.py
import json
from src.exchange_api.high_liquidity_exchanges.base_high_liquidity_exchange import BaseHighLiquidityExchange
from src.exchange_api.utils import load_api_keys, handle_api_response
from src.exchange_api.high_liquidity_exchanges import encoders
from typing import List, Dict, Optional, Union
from urllib.parse import urlencode
import requests
import hashlib
import logging
import inspect
import time
import hmac

logger = logging.getLogger(__name__)


class BinanceProxy(BaseHighLiquidityExchange):
    """
    Proxy class for interacting with the Binance API.
    """
    BASE_URL = "https://api.binance.com"
    BASE_URL_PUBLIC = "https://data-api.binance.vision"
    ENDPOINTS = {
        "ALL_COINS_INFO": "/sapi/v1/capital/config/getall",
        "DEPOSIT_ADDRESS": "/sapi/v1/capital/deposit/address",
        "WITHDRAW_REQUEST": "/sapi/v1/capital/withdraw/apply",
        "TIME": "/api/v3/time",
        'NEW_ORDER': '/api/v3/order',
        'CANCEL_ORDER': '/api/v3/order',
        'WITHDRAW_HISTORY': '/sapi/v1/capital/withdraw/history',
        "DEPOSIT_HISTORY": "/sapi/v1/capital/deposit/hisrec",
        "PRICE": "/api/v3/ticker/price?symbol={}",
        "MARKET": "/api/v3/exchangeInfo?symbol={}"
    }

    def __init__(self) -> None:
        """
        Initialize the BinanceProxy with API key and secret.
        """
        self.api_key, self.api_secret = load_api_keys("BINANCE")
        self.name: str = "BINANCE"

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

    def _get_server_time(self) -> int:
        """
        Fetch the current server time from Binance.
        :return: Server time in milliseconds.
        """
        url = f"{self.BASE_URL}{self.ENDPOINTS['TIME']}"
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)["serverTime"]
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching sever time from Binance: {e}")
            raise

    def check_datetime_differences(self) -> None:
        """
        Check if the local system clock is accurate by comparing it to Binance’s server time:
        :return:
        """
        local_time = int(time.time() * 1000)
        binance_time = self._get_server_time()
        time_difference = abs(local_time - binance_time)
        print(f"Time difference: {time_difference} ms")

    def get_coin_info(self, coin: Optional[str] = None) -> Union[Dict, List[Dict]]:
        """
        Fetch information of all coins from Binance API.
        If a coin's name is provided, returns only the coin's information.

        :param coin: str representing the name of the coin.
        :return: List of dictionaries containing coin information.
        """
        current_method_name = inspect.currentframe().f_code.co_name

        url = f"{self.BASE_URL}{self.ENDPOINTS['ALL_COINS_INFO']}"
        headers = {"X-MBX-APIKEY": self.api_key}
        params = self._sign_request({})
        try:
            response = requests.get(url, headers=headers, params=params)
            # Use the standard response handler to handle errors and responses
            response = handle_api_response(response)
            if coin:
                coins_info = response
                for coin_info in coins_info:
                    if coin_info.get("coin") == coin.upper():
                        # Uncomment to display the response
                        # print(json.dumps(coin_info, indent=2))
                        return coin_info
            else:
                return response

        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching cpin information from Binance: {e}")
            raise

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

    def get_withdraw_history(self, coin: Optional[str] = None, withdraw_order_id: Optional[str] = None) -> List[Dict]:
        """
        Get the withdrawal history of a given coin, or a given order.

        :param coin: Coin of interest
        :param withdraw_order_id: id of a specific order
        :return: Withdrawal history
        """
        current_method_name = inspect.currentframe().f_code.co_name

        url = f"{self.BASE_URL}{self.ENDPOINTS['WITHDRAW_HISTORY']}"
        headers = {"X-MBX-APIKEY": self.api_key}

        params = {
            "coin": coin,
            } if coin else {}

        # TODO: FIX: Now if withdrawOrderId is provided, returns an empty list
        if withdraw_order_id:
            params['withdrawOrderId'] = str(withdraw_order_id)

        params['timestamp'] = int(time.time() * 1000)
        params = self._sign_request(params)
        try:
            response = requests.get(url, headers=headers, params=params)
            # Use the standard response handler to handle errors and responses
            response = handle_api_response(response)
            for withdraw in response:
                status = withdraw['status']
                state = encoders.binance_withdrawal_states.get(status)
                withdraw['state'] = state
            return response
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching withdrawal history from Binance: {e}")
            raise

    def get_deposit_history(self, coin: Optional[str] = None) -> List[Dict]:
        """
        Get the deposit history of a given coin, or a given order.

        :param coin: Coin of interest
        :return: Deposit history
        """
        url = f"{self.BASE_URL}{self.ENDPOINTS['DEPOSIT_HISTORY']}"
        headers = {"X-MBX-APIKEY": self.api_key}

        params = {
            "includeSource": True,
            "timestamp": int(time.time() * 1000),
            }

        if coin:
            params['coin'] = coin

        params = self._sign_request(params)

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url, headers=headers, params=params)
            # Use the standard response handler to handle errors and responses
            response = handle_api_response(response)
            for deposit in response:
                status = deposit['status']
                state = encoders.binance_deposit_states.get(status)
                deposit['state'] = state
            return response
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching deposit history from Binance: {e}")
            raise

    def create_deposit_address(
            self,
            coin: str,
            network: str,
            amount: Optional[float] = None) -> Dict:
        """
        Fetch a deposit address for a specific coin and network.

        :param coin: The symbol of the cryptocurrency (e.g., 'BTC').
        :param network: The network to use for the deposit (e.g., 'BTC', 'LIGHTNING'). If not provided, the default network is used.
        :param amount: The amount to deposit (only required for LIGHTNING network).
        :return: A dictionary containing the deposit address and related details.
        :raises Exception: If the request fails or the response contains an error.
        """
        network = network.upper() if network else network

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

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url, headers=headers, params=signed_params)
            # Use the standard response handler to handle errors and responses
            response = handle_api_response(response)
            if self._validate_deposit_availability(coin, network_name=network):
                return response
            else:
                logger.error(f"Deposit address is not available, got this response:")
                raise Exception(f"Error for deposit address {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching deposit address from Binance: {e}")
            raise

    def _validate_deposit_availability(self, coin: str, network_name: str) -> bool:
        """
        Check the availability of a given crypto address

        :param coin: Coin to deposit
        :param network_name: network to check
        :return: True if it is available, False otherwise
        """
        coins_info = self.get_coin_info()
        for coin_info in coins_info:
            if coin_info.get("coin") == coin:
                # Uncomment to display the response
                # print(json.dumps(coin_info, indent=2))
                for network in coin_info.get("networkList", []):
                    if network_name in network.get("network", ""):
                        return network.get("depositEnable", False)
        return False

    def create_quote_currency_address(self,
                                      coin: str,
                                      network: Optional[str] = None) -> Dict:
        """
        Create a deposit address for any available alt_coin.

        :param coin: The cryptocurrency symbol.
        :param network: The network for the deposit.
        """
        response = self.create_deposit_address(coin=coin, network=network)
        return {"address": response.get('address')}

    def create_lightning_invoice(
            self,
            amount: float
    ) -> Dict:
        """
        Create a lightning invoice for a given amount.

        :param amount: The amount to deposit (in BTC fractions).
        :return: A dictionary containing the deposit address and related details.
        :raises Exception: If the request fails or the response contains an error.
        """
        coin = 'BTC'
        network = "LIGHTNING"

        try:
            invoice_info = self.create_deposit_address(coin=coin, amount=amount, network=network)
            coin = invoice_info.get("coin")
            invoice = invoice_info.get("address")
            standardized_response = {
                'coin': coin,
                'invoice': invoice,
                'amount': amount
            }
            return standardized_response
        except Exception:
            logging.error("Error while creating LN invoice in BINANCE")
            return False

    def create_withdraw_request(self, coin: str, address: str, amount: float,
                                network: Optional[str] = "LIGHTNING", wallet_type: Optional[int] = 0, **kwargs) -> Dict:
        """
        Submit a withdrawal request to Binance.

        :param coin: The symbol of the cryptocurrency to withdraw (e.g., 'BTC').
        :param address: The destination address for the withdrawal.
        :param amount: The amount of cryptocurrency to withdraw.
        :param network: Optional, the network to use for withdrawal.
        :param wallet_type: The wallet type for withdraw，0-spot wallet ，1-funding wallet.
        :param kwargs: Additional optional parameters (e.g., withdrawOrderId, addressTag, transactionFeeFlag, name).
        :return: A dictionary containing the withdrawal request ID.
        :raises Exception: If the request fails or the response contains an error.
        """

        if coin.upper() == "BTC":
            fee = 0.000001  # From coins_info
            amount += fee

        params = {
            "coin": coin,
            "address": address,
            "amount": amount,
            "timestamp": int(time.time() * 1000),
            "walletType": wallet_type
        }

        if network:
            params["network"] = network

        # Add additional optional parameters from kwargs
        optional_fields = ["withdrawOrderId", "addressTag", "transactionFeeFlag", "name", "recvWindow"]
        for field in optional_fields:
            if field in kwargs:
                params[field] = kwargs[field]

        # Sign the request
        signed_params = self._sign_request(params)

        # Make the API request
        url = f"{self.BASE_URL}{self.ENDPOINTS['WITHDRAW_REQUEST']}"
        headers = {"X-MBX-APIKEY": self.api_key}

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.post(url, headers=headers, params=signed_params)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching withdrawal request from Binance: {e}")
            raise

    def pay_ln_invoice(self, ln_invoice: str, amount: float,
                       wallet_type: Optional[int] = 0, **kwargs) -> Dict:
        """
        Submit a withdrawal request in Binance for BTC, via Lightning Network.

        :param ln_invoice: The destination address for the withdrawal (Lightning Network Invoice).
        :param amount: The withdrawal amount (in fractions of BTC).
        :param wallet_type: The wallet type for withdraw，0-spot wallet ，1-funding wallet.
        :param kwargs: Additional optional parameters (e.g., withdrawOrderId, addressTag, transactionFeeFlag, name).
        :return: A dictionary containing the withdrawal request ID.
        :raises Exception: If the request fails or the response contains an error.
        """
        coin = "BTC"
        network = "LIGHTNING"
        return self.create_withdraw_request(coin=coin,
                                            address=ln_invoice,
                                            amount=amount,
                                            wallet_type=wallet_type,
                                            network=network)

    def new_order(self, base_currency: str, quote_currency: str, side: str, order_type: str,
                  timestamp: Optional[int] = None,
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
        """
        Create a new order on Binance using the specified parameters.

        :param base_currency: The base currency in of the trading pair (e.g., 'BTC' in 'BTCUSDT').
        :param quote_currency: The base currency in of the trading pair (e.g., 'USDT' in 'BTCUSDT').
        :param side: The side of the order (BUY or SELL).
        :param order_type: The type of the order (LIMIT, MARKET, STOP_LOSS, etc.).
        :param quantity: The quantity to buy or sell. (Optional, depends on order type).
        :param price: The price for LIMIT orders. (Optional, depends on order type).
        :param time_in_force: The time-in-force for LIMIT orders. (Optional, depends on order type).
        :param stop_price: The stop price for stop-loss or take-profit orders. (Optional).
        :param iceberg_qty: The quantity for iceberg orders. (Optional).
        :param quote_order_qty: The quote asset quantity for MARKET orders. (Optional).
        :param new_client_order_id: A unique client order ID. (Optional).
        :param strategy_id: The strategy ID if applicable. (Optional).
        :param strategy_type: The strategy type ID if applicable. (Optional).
        :param trailing_delta: The trailing delta for stop loss and take profit. (Optional).
        :param new_order_resp_type: The response type (ACK, RESULT, or FULL). (Optional).
        :param self_trade_prevention_mode: Self trade prevention mode. (Optional).
        :param recv_window: The receiving window for the request. (Optional).
        :param timestamp: The timestamp for the request. (Required).
        :return: The response from the exchange API as a dictionary.
        """
        timestamp = int(time.time() * 1000)
        symbol = base_currency.upper() + quote_currency.upper()
        # Construct the query parameters
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'timestamp': timestamp,
        }

        if quantity is not None:
            params['quantity'] = quantity
        if price is not None:
            params['price'] = price
        if time_in_force is not None:
            params['timeInForce'] = time_in_force
        if stop_price is not None:
            params['stopPrice'] = stop_price
        if iceberg_qty is not None:
            params['icebergQty'] = iceberg_qty
        if quote_order_qty is not None:
            params['quoteOrderQty'] = quote_order_qty
        if new_client_order_id is not None:
            params['newClientOrderId'] = new_client_order_id
        if strategy_id is not None:
            params['strategyId'] = strategy_id
        if strategy_type is not None:
            params['strategyType'] = strategy_type
        if trailing_delta is not None:
            params['trailingDelta'] = trailing_delta
        if new_order_resp_type is not None:
            params['newOrderRespType'] = new_order_resp_type
        if self_trade_prevention_mode is not None:
            params['selfTradePreventionMode'] = self_trade_prevention_mode
        if recv_window is not None:
            params['recvWindow'] = recv_window

        # Sign the request
        signed_params = self._sign_request(params)

        # Make the API request
        url = f"{self.BASE_URL}{self.ENDPOINTS['NEW_ORDER']}"
        headers = {"X-MBX-APIKEY": self.api_key}

        try:
            response = requests.post(url, headers=headers, params=signed_params)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            current_method_name = inspect.currentframe().f_code.co_name
            logger.error(f"{current_method_name} - Error fetching new order request from Binance: {e}")
            raise

    def cancel_order(self, base_currency: str, quote_currency: str, order_id: int) -> Dict:
        """
        Cancel an order given its id.

        :param base_currency: The base currency in of the trading pair (e.g., 'BTC' in 'BTCUSDT').
        :param quote_currency: The base currency in of the trading pair (e.g., 'USDT' in 'BTCUSDT').
        :param order_id: identification of the order to cancel.

        :return: The response from the exchange API as a dictionary.
        """

        symbol = base_currency.upper() + quote_currency.upper()
        # Construct the query parameters
        params = {
            'symbol': symbol,
            'orderId': order_id,
        }

        # Sign the request
        signed_params = self._sign_request(params)

        # Make the API request
        url = f"{self.BASE_URL}{self.ENDPOINTS['NEW_ORDER']}"
        headers = {"X-MBX-APIKEY": self.api_key}
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.delete(url, headers=headers, params=signed_params)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching cancel order request from Binance: {e}")
            raise

    def get_price(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Retrieve the price of an asset in a specified market.

        :param base_currency: The base currency of the trading pair (e.g., 'BTC').
        :param quote_currency: The quote currency of the trading pair (e.g., 'USD').
        :return: A dictionary containing the price information.
        :raises Exception: If the API request fails.
        """
        symbol = base_currency.upper() + quote_currency.upper()

        # Make the API request
        url = f"{self.BASE_URL_PUBLIC}{self.ENDPOINTS['PRICE'].format(symbol)}"

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching asset price from Binance: {e}")
            raise

    def get_market_info(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Retrieve the market information of the market f'{base_currency.upper()}{quote_currency.upper()}'.

        :param base_currency: The base currency of the trading pair (e.g., 'BTC').
        :param quote_currency: The quote currency of the trading pair (e.g., 'USDC').
        :return: A dictionary containing the market information.
        """
        symbol = base_currency.upper() + quote_currency.upper()

        # Make the API request
        url = f"{self.BASE_URL_PUBLIC}{self.ENDPOINTS['MARKET'].format(symbol)}"

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching market info  from Binance: {e}")
            raise
