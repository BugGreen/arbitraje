# exchange_api/buda_proxy.py
from src.exchange_api.low_liquidity_exchanges.base_low_liquidity_exchange import BaseLowLiquidityExchange
from src.exchange_api.utils import load_api_keys, handle_api_response
from typing import List, Dict, Optional, Union, Any
import requests
import logging
import hashlib
import inspect
import base64
import json
import time
import hmac


logger = logging.getLogger(__name__)


class BudaProxy(BaseLowLiquidityExchange):
    """
    Proxy class for interacting with the BUDA API.
    """

    def __init__(self) -> None:
        """
        Initialize the BudaProxy with API key and secret.
        """
        self.api_key, self.api_secret = load_api_keys("BUDA")
        self.name: str = "BUDA"

    BASE_URL = "https://www.buda.com"
    ENDPOINTS = {
        "LIGHTNING_INVOICE": "/api/v2/lightning_network_invoices",
        "LIGHTNING_WITHDRAWAL": "/api/v2/reserves/ln-btc/withdrawals",
        "NEW_ORDER": "/api/v2/markets/{}/orders",
        "CANCEL_ORDER": "/api/v2/orders/{}",
        "ORDER_STATES": "/api/v2/markets/{}/orders",
        "BATCH_ORDERS": "/api/v2/orders",
        "CRYPTO_WITHDRAWAL": "/api/v2/currencies/{currency}/withdrawals",
        "ORDER_BOOK": "/api/v2/markets/{}/order_book",
        "WITHDRAW_HISTORY": "/api/v2/currencies/{}/{}",
        "ADDRESS_ID": "/api/v2/currencies/{}/receive_addresses",
        "DEPOSIT_ADDRESS": "/api/v2/currencies/{}/receive_addresses/{}",
        "PRICE": "/api/v2/markets/{}/ticker",
        "MARKETS": "/api/v2/markets/{}",
        "BALANCES": "/api/v2/balances/{}"
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
            string_to_sign = f"{method} {path} {base64_encoded_body} {nonce}"

        else:
            string_to_sign = f"{method} {path} {nonce}"

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

    @staticmethod
    def _translate_batch_response(response: Union[Dict[str, Any], Exception]) \
            -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Translate Buda's response into a standardized format.

        :param response: The raw response from Buda or an Exception.
        :return: Standardized response.
        """
        if isinstance(response, Exception):
            logger.error("Exception during Buda batch_creation: %s", response)
            return {
                "error_code": "EXCHANGE_HTTP_ERROR",
                "message": str(response)
            }

        if "orders_diff" not in response:
            # It's an API-level error
            logger.error("Placement of order batch was not possible")
            error_code = response.get("code", "UNKNOWN_ERROR")
            message = response.get("message", "An unknown error occurred.")
            details = response.get("errors", [])
            return {
                "error_code": f"EXCHANGE_API_ERROR_{error_code}",
                "message": message,
                "details": details
            }

        standardized_orders = []
        for order_diff in response.get("orders_diff", []):
            order = order_diff.get("order", {})
            order_details = order.get("order", {})

            order_id = order_details.get("id") if order_details.get("id") else None
            state = order_details.get("state", "error")
            error_msg = order_details.get("message")
            amount = order_details.get("amount")
            traded_amount = order_details.get("traded_amount")
            total_exchanged = order_details.get("total_exchanged")

            # Map Buda's 'state' field to a unified 'status'
            if state in ("received", "pending", "traded", "canceled"):
                status = state
            elif state == "unprepared":
                # MEANING: Insolvent error
                logger.error("Insolvent error, for amount: %s", str(amount))
                status = "unprepared"
            else:
                status = "error"

            standardized_orders.append({
                "id": order_id,
                "status": status,
                "error_message": error_msg,
                "amount": amount,
                "traded_amount": traded_amount,
                "total_exchanged": total_exchanged
            })

        return standardized_orders

    def get_balances(self, coin: Optional[str] = "") -> Dict[str, List]:
        """
        Get account's balance for each currency.

        :param coin: If no currency is provided then all currencies are considered
        :return: Account's balance.
        """
        # Define the endpoint path for retrieving the order book
        endpoint_path = self.ENDPOINTS["BALANCES"].format(coin.lower()).rstrip("/")
        url = f"{self.BASE_URL}{endpoint_path}"

        # Sign the request (assuming _sign_request can handle GET without body)
        headers = self._sign_request(method="GET", path=endpoint_path)

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url, headers=headers)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching balance information request from Buda: {e}")
            raise

    def batch_creation(self, orders: List[Dict[str, Any]]) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Create new orders in batch on the Buda exchange.

        :param orders: A list of orders to be created, where each order is a dictionary containing order details.
        :return: A standardized response indicating success or error.
        """
        endpoint_path = self.ENDPOINTS["BATCH_ORDERS"]
        url = f"{self.BASE_URL}{endpoint_path}"

        payload = {'diff': []}
        for order in orders:
            if order.get("mode") == "place":
                payload['diff'].append({
                    'mode': 'place',
                    'order': order.get('order')
                })

        headers = self._sign_request(method="POST", path=endpoint_path, body=payload)

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)  # Added timeout
            return self._translate_batch_response(response.json())
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error during Buda batch_creation: %s", http_err)
            return {
                "error_code": "HTTP_ERROR",
                "message": str(http_err),
                "status_code": response.status_code
            }
        except requests.exceptions.RequestException as req_err:
            logger.error("Request exception during Buda batch_creation: %s", req_err)
            return {
                "error_code": "REQUEST_EXCEPTION",
                "message": str(req_err)
            }
        except Exception as e:
            logger.error("Unexpected exception during Buda batch_creation: %s", e, exc_info=True)
            return {
                "error_code": "UNKNOWN_ERROR",
                "message": str(e)
            }

    def get_order_book(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Retrieve the current order book for a specified market.

        :param base_currency: The base currency of the trading pair (e.g., 'BTC').
        :param quote_currency: The quote currency of the trading pair (e.g., 'USD').
        :return: A dictionary containing 'asks' and 'bids' lists from the order book.
        :raises Exception: If the API request fails.
        """
        market_id = "-".join([base_currency.lower(), quote_currency.lower()])

        # Define the endpoint path for retrieving the order book
        endpoint_path = self.ENDPOINTS["ORDER_BOOK"].format(market_id)
        url = f"{self.BASE_URL}{endpoint_path}"

        # Sign the request (assuming _sign_request can handle GET without body)
        headers = self._sign_request(method="GET", path=endpoint_path)

        # Make the API call to retrieve the order book

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url, headers=headers)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching order book request from Buda: {e}")
            raise

    def get_market_info(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Retrieve the market information of the market f'{base_currency}-{quote_currency}'.

        :param base_currency: The base currency of the trading pair (e.g., 'BTC').
        :param quote_currency: The quote currency of the trading pair (e.g., 'USDC').
        :return: A dictionary containing the market information.
        :raises Exception: If the API request fails.
        """
        market_id = "-".join([base_currency.lower(), quote_currency.lower()])

        # Define the endpoint path for retrieving the order book
        endpoint_path = self.ENDPOINTS["MARKETS"].format(market_id)
        url = f"{self.BASE_URL}{endpoint_path}"

        # Sign the request (assuming _sign_request can handle GET without body)
        headers = self._sign_request(method="GET", path=endpoint_path)

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url, headers=headers)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching market information request from Buda: {e}")
            raise

    def _get_withdraw_or_deposit_history(self, coin: str, direction: str) -> Dict[str, List[Dict]]:
        """
        Get the Deposit/Withdrawal history of a given coin, or a given order.

        :param coin: Coin of interest
        :param direction: deposits/withdrawals
        :return: Deposit/Withdrawal history
        """
        coin = coin.upper()

        # Define the endpoint path for retrieving the order book
        endpoint_path = self.ENDPOINTS["WITHDRAW_HISTORY"].format(coin, direction)
        url = f"{self.BASE_URL}{endpoint_path}"

        # Sign the request (assuming _sign_request can handle GET without body)
        headers = self._sign_request(method="GET", path=endpoint_path)

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url, headers=headers)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching withdraw/deposit history request from Buda: {e}")
            raise

    def get_withdraw_history(self, coin: str) -> List[Dict]:
        """
        Get the withdrawal history of a given coin, or a given order.

        :param coin: Coin of interest
        :return: Deposit/Withdrawal history
        """
        direction = "withdrawals"
        withdraw_history = self._get_withdraw_or_deposit_history(coin=coin, direction=direction).get(direction)
        return withdraw_history

    def get_deposit_history(self, coin: str) -> List[Dict]:
        """
        Get the deposit history of a given coin, or a given order.

        :param coin: Coin of interest
        :return: Deposit history
        """
        direction = "deposits"
        withdraw_history = self._get_withdraw_or_deposit_history(coin=coin, direction=direction).get(direction)
        return withdraw_history

    def create_deposit_address(self, coin: str = "BTC", network: Optional[str] = "lightning",
                               amount_satoshis: Optional[int] = 0, memo: Optional[str] = None,
                               expiry_seconds: Optional[int] = 0) -> Dict:
        """
        # TODO: Ajustar el parametro `network` para cuando la red SOL esté habilitada
        Create a deposit address (invoice if BTC) for any available crypto.

        :param coin: The cryptocurrency symbol (e.g., 'BTC'). Must be 'BTC' for Lightning Network.
        :param network: The network for the deposit. If provided, must be 'lightning'.
        :param amount_satoshis: The amount of the invoice in satoshis.
        :param memo: Optional brief description for the invoice.
        :param expiry_seconds: Optional expiry time for the invoice in seconds.
        :return: A dictionary containing the encoded payment request.
        :raises Exception: If the request fails or the response contains an error.
        """
        coin = coin.lower()

        if coin == 'btc':

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

        elif coin in ['eth', 'ltc', 'bch', 'usdc', 'usdt']:
            response = self._create_altcoin_address(coin)
            if not self._validate_address_availability(response):
                logger.error(f"Deposit address is not available, got this response:")
                raise Exception(f"Error for deposit address {response.status_code}: {response.text}")
        else:
            raise ValueError(f"Error coin {coin.upper()} is not supported")

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response: Dict = handle_api_response(response)
            if coin == 'btc':
                response = response.get("invoice", {})
            else:
                response = response
            return response
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching deposit address request from Buda: {e}")
            raise

    def _create_altcoin_address(self, coin: str) -> str:
        """
        Create a new altcoin address

        :param coin: Acronym of the currency being deposited
        :return: the id
        """
        endpoint_path = self.ENDPOINTS["ADDRESS_ID"].format(coin)
        url = f"{self.BASE_URL}{endpoint_path}"
        # Authenticate the request
        headers = self._sign_request(method="POST", path=endpoint_path)

        # Handle the response
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.post(url, headers=headers)
            # Use the standard response handler to handle errors and responses
            handle_api_response(response)
            return response
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching {coin} address request from Buda: {e}")
            raise

    def create_quote_currency_address(self,
                                      coin: str,
                                      network: Optional[str] = None) -> Dict:
        """
        Create a deposit address for any available alt_coin.

        :param coin: The cryptocurrency symbol.
        :param network: The network for the deposit.
        """
        response = self.create_deposit_address(coin=coin, network=network)
        return {"address": response.get("receive_address").get('address')}

    @staticmethod
    def _validate_address_availability(address_creation_response: dict) -> bool:
        """
        Check the availability of a given crypto address

        :param address_creation_response: response object
        :return: True if it is available, False otherwise
        """
        address_creation_response = address_creation_response.json()
        available = address_creation_response.get("receive_address", {}).get("ready", False)
        if available:
            return True
        else:
            False

    def create_lightning_invoice(self,
                                 amount: float,
                                 memo: Optional[str] = None,
                                 expiry_seconds: Optional[int] = 0) -> Dict:
        """
        Create a Lightning Network deposit address (invoice) for BTC for a given amount.

        :param amount: The amount to deposit (in BTC fractions).
        :param memo: Optional brief description for the invoice.
        :param expiry_seconds: Optional expiry time for the invoice in seconds.
        :return: A dictionary containing the encoded payment request.
        :raises Exception: If the request fails or the response contains an error.
        """
        coin = 'BTC'
        network = "lightning"
        amount_sats = amount * 100000000

        # Define the endpoint path
        endpoint_path = self.ENDPOINTS["LIGHTNING_INVOICE"]
        url = f"{self.BASE_URL}{endpoint_path}"

        # Build the payload
        payload = {
            "amount_satoshis": amount_sats,
            "currency": "BTC"
        }
        if memo:
            payload["memo"] = memo
        if expiry_seconds:
            payload["expiry_seconds"] = expiry_seconds

        # Authenticate the request
        headers = self._sign_request(method="POST", path=endpoint_path, body=payload if payload else "")

        # Make the API call

        # Handle the response

        # Handle the response
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.post(url, headers=headers, json=payload)
            # Use the standard response handler to handle errors and responses
            response: Dict = handle_api_response(response)
            invoice_info = response.get("invoice", {})
            coin = invoice_info.get("currency")
            invoice = invoice_info.get("encoded_payment_request")
            standardized_response = {
                'coin': coin,
                'invoice': invoice,
                'amount': amount
            }
            return standardized_response
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching ln invoice creation request from Buda: {e}")
            raise

    def create_withdraw_request(self, coin: str, address: str, amount: float,
                                simulate: Optional[bool] = False, network: Optional[bool] = False,
                                priority: Optional[bool] = True) -> Dict:
        """
        Submit a withdrawal request for a selected cryptocurrency (BTC, ETH, USDC, BCH, LTC).


        :param coin: The cryptocurrency symbol (e.g., 'BTC', 'ETH', 'USDC', 'BCH', 'LTC').
        :param address: The target address (for crypto transfers) or payment request (for Lightning Network).
        :param amount: The withdrawal amount.
        :param simulate: Optional flag to simulate the payment request without executing it.
        :param network: Optional, the network to use for withdrawal.
        :param priority: Optional, True for a priority withdrawal.
        :return: A dictionary containing the details of the withdrawal request.
        :raises ValueError: If the coin is unsupported or if incorrect parameters are provided.
        :raises Exception: If the request fails or the response contains an error.
        """

        # Handling Lightning Network withdrawal for BTC
        if coin.upper() == "BTC":
            # Define the endpoint path for Lightning Network
            endpoint_path = self.ENDPOINTS["LIGHTNING_WITHDRAWAL"]
            url = f"{self.BASE_URL}{endpoint_path}"
            withdrawal_data = {"payment_request": address}

        # Handling traditional crypto withdrawals (ETH, USDC, BCH, LTC)
        elif coin.upper() in ['ETH', 'USDC', 'BCH', 'LTC']:
            # Define the endpoint path for traditional crypto withdrawals
            endpoint_path = self.ENDPOINTS["CRYPTO_WITHDRAWAL"].format(currency=coin.lower())
            url = f"{self.BASE_URL}{endpoint_path}"
            withdrawal_data = {
                "target_address": address,
                "priority": priority
            }

        else:
            # Raise an error if the coin is unsupported
            raise ValueError(f"Withdrawal not supported for the cryptocurrency {coin.upper()}.")
        payload = {
            "amount": amount,
            "withdrawal_data": withdrawal_data,
            "simulate": simulate
        }
        # Sign the request
        headers = self._sign_request(method="POST", path=endpoint_path, body=payload)

        # Make the API call
        # Handle the response
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.post(url, headers=headers, json=payload)
            # Use the standard response handler to handle errors and responses
            response: Dict = handle_api_response(response)
            return response.get("withdrawal")
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching {coin} address request from Buda: {e}")
            raise

    def pay_ln_invoice(self, ln_invoice: str, amount: float, simulate: bool = False) -> Dict:
        """
        Submit a withdrawal request for BTC, via Lightning Network.

        :param ln_invoice: The payment request (Lightning Network Invoice).
        :param amount: The withdrawal amount (in fractions of BTC).
        :param simulate: Optional flag to simulate the payment request without executing it.
        :return: A dictionary containing the details of the withdrawal request.
        :raises ValueError: If the coin is unsupported or if incorrect parameters are provided.
        :raises Exception: If the request fails or the response contains an error.
        """

        coin = 'BTC'
        withdraw_info = self.create_withdraw_request(coin=coin, address=ln_invoice, amount=amount, simulate=simulate)
        return {"id": withdraw_info.get("id")}

    def new_order(self, base_currency: str, quote_currency: str, side: str, order_type: str, amount: float,
                  price: Optional[float] = None,
                  stop_price: Optional[float] = None,
                  order_limit_type: Optional[str] = "gtc",
                  stop_order_type: Optional[str] = None,
                  client_id: Optional[str] = None) -> Dict:
        """
        Create a new order on Buda using the specified parameters.

        :param base_currency: The base currency in of the trading pair (e.g., 'btc' in 'btc-clp').
        :param quote_currency: The base currency in of the trading pair (e.g., 'clp' in 'btc-clp').
        :param side: The side of the order (Bid or Ask).
        :param order_type: The type of the order (limit or market).
        :param amount: The amount of the asset to buy or sell.
        :param price: The price for limit orders (optional).
        :param stop_price: The stop price for stop orders (optional).
        :param order_limit_type: The type of limit order (e.g., gtc, ioc, fok, post_only).
        :param stop_order_type: The type of stop order (e.g., stop_loss, take_profit).
        :param client_id: A unique client ID for the order (optional).
        :return: The response from the exchange API as a dictionary.
        """

        market_id = "-".join([base_currency.lower(), quote_currency.lower()])
        # Define the endpoint path
        endpoint_path = f"{self.ENDPOINTS['NEW_ORDER'].format(market_id)}"
        url = f"{self.BASE_URL}{endpoint_path}"

        # Prepare the request payload
        payload = {
            'type': side.title(),  # 'Bid' or 'Ask'
            'price_type': order_type.lower(),  # 'limit' or 'market'
            'amount': float(amount),
            'client_id': client_id if client_id else None  # Optional client ID
        }

        if order_type == 'limit':
            payload['limit'] = {'price': price, 'type': order_limit_type}  # Limit price and order type (gtc, ioc, etc.)

        if stop_price is not None:
            payload['stop'] = {'stop_price': stop_price, 'type': stop_order_type}  # Stop order details

        # Authenticate the request
        headers = self._sign_request(method="POST", path=endpoint_path, body=payload)

        # Make the API call
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.post(url, headers=headers, json=payload)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching new order request from Buda: {e} \n "
                         f"Payload: {payload}")
            raise

    def cancel_order(self, base_currency: str, quote_currency: str, order_id: int) -> Dict:
        """
        Cancel an existing order on Buda exchange.

        :param base_currency: The base currency of the trading pair (e.g., 'btc' in 'btc-clp').
        :param quote_currency: The quote currency of the trading pair (e.g., 'clp' in 'btc-clp').
        :param order_id: The ID of the order to be canceled.
        :return: The response from the exchange API as a dictionary containing order details after cancellation.
        """

        market_id = "-".join([base_currency.lower(), quote_currency.lower()])

        # Define the endpoint path for canceling the order
        endpoint_path = self.ENDPOINTS["CANCEL_ORDER"].format(order_id)
        url = f"{self.BASE_URL}{endpoint_path}"

        # Prepare the request payload to cancel the order
        payload = {
            'state': 'canceling'  # Must indicate that the order is in the process of being canceled
        }

        # Sign the request
        headers = self._sign_request(method="PUT", path=endpoint_path, body=payload)

        # Make the API call to cancel the order

        # Return the response as a dictionary
        # Make the API call
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.put(url, headers=headers, json=payload)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching cancel order request from Buda: {e} \n "
                         f"Payload: {payload}")
            raise

    def cancel_all_orders(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Cancel an existing order on Buda exchange.

        :param base_currency: The base currency of the trading pair (e.g., 'btc' in 'btc-clp').
        :param quote_currency: The quote currency of the trading pair (e.g., 'clp' in 'btc-clp').
        :param order_id: The ID of the order to be canceled.
        :return: The response from the exchange API as a dictionary containing order details after cancellation.
        """

        market_id = "-".join([base_currency.lower(), quote_currency.lower()]) if base_currency and quote_currency \
            else ""

        # Define the endpoint path for canceling the order
        endpoint_path = self.ENDPOINTS["CANCEL_ORDER"].rstrip("/{}")

        url = f"{self.BASE_URL}{endpoint_path}"

        # Prepare the request payload to cancel the order
        payload = {
            'market': market_id,
        } if market_id else {}

        # Sign the request
        headers = self._sign_request(method="DELETE", path=endpoint_path, body=payload)

        # Make the API call to cancel the order

        # Return the response as a dictionary
        # Make the API call
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.delete(url, headers=headers, json=payload)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching cancel all orders request from Buda: {e} \n "
                         f"Payload: {payload}")
            raise

    def get_order_states(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Get the states of orders in a given market.
        Possible states are: received, pending, active, traded, canceled, canceled_and_traded, unprepared

        :param base_currency: The base currency in of the trading pair (e.g., 'BTC' in 'BTCUSDT').
        :param quote_currency: The base currency in of the trading pair (e.g., 'USDT' in 'BTCUSDT').

        :return: The response from the exchange API as a dictionary.
        """

        market_id = "-".join([base_currency.lower(), quote_currency.lower()])

        # Define the endpoint path for canceling the order
        endpoint_path = self.ENDPOINTS["ORDER_STATES"].format(market_id)
        url = f"{self.BASE_URL}{endpoint_path}"

        # Sign the request
        headers = self._sign_request(method="GET", path=endpoint_path)

        # Return the response as a dictionary
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url, headers=headers)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching cancel order request from Buda: {e}")
            raise

    def batch_cancellation(self, orders: List[Dict]) -> Dict:
        """
        Cancel orders in batch on the Buda exchange.

        :param orders: A list of orders to be canceled, where each order is a dictionary containing 'order_id' or 'client_id'.
        :return: The response from the exchange API indicating whether the batch cancelation was successful.
        """

        # Define the endpoint path
        endpoint_path = self.ENDPOINTS["BATCH_ORDERS"]
        url = f"{self.BASE_URL}{endpoint_path}"

        # Prepare the request payload
        payload = {'diff': []}

        # Add 'cancel' orders to the payload
        for order in orders:
            if order.get("mode") == "cancel":
                if 'order_id' in order:
                    payload['diff'].append({
                        'mode': 'cancel',
                        'order_id': order.get('order_id')
                    })
                elif 'client_id' in order:
                    payload['diff'].append({
                        'mode': 'cancel',
                        'client_id': order.get('client_id')
                    })

        # Sign the request
        headers = self._sign_request(method="POST", path=endpoint_path, body=payload)
        # Make the API call to cancel the batch orders

        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.post(url, headers=headers, json=payload)
            # Use the standard response handler to handle errors and responses
            return handle_api_response(response)
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching batch cancellation request from Buda: {e} \n "
                         f"Payload: {payload}")
            raise
        return response.json()

    def get_price(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Retrieve the price of an asset in a specified market.

        :param base_currency: The base currency of the trading pair (e.g., 'BTC').
        :param quote_currency: The quote currency of the trading pair (e.g., 'USD').
        :return: A dictionary containing the price information.
        :raises Exception: If the API request fails.
        """
        symbol = base_currency.lower() + '-' + quote_currency.lower()

        # Define the endpoint path
        endpoint_path = self.ENDPOINTS["PRICE"].format(symbol)
        url = f"{self.BASE_URL}{endpoint_path}"
        # Return the response as a dictionary
        current_method_name = inspect.currentframe().f_code.co_name
        try:
            response = requests.get(url)
            response: Dict = handle_api_response(response)
            info = response.get('ticker')
            symbol: str = info.get("market_id")
            last_price: str = info.get("last_price")[0]

            price_info = {
                'symbol': symbol.replace("-", ''),
                'price': last_price
            }
            return price_info
        except Exception as e:
            logger.error(f"{current_method_name} - Error fetching price information ({symbol}) request from Buda: {e}")
            raise

