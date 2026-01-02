from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseExchange(ABC):
    """
    Abstract base class defining the interface for exchange proxies.
    """

    @abstractmethod
    def get_withdraw_history(self, coin: Optional[str]) -> List[Dict]:
        """
        Get the withdrawal history of a given coin, or a given order.

        :param coin: Coin of interest
        :return: Withdrawal history
        """
        pass

    @abstractmethod
    def get_deposit_history(self, coin: Optional[str]) -> List[Dict]:
        """
        Get the deposit history of a given coin, or a given order.

        :param coin: Coin of interest
        :return: Deposit history
        """
        pass

    @abstractmethod
    def create_deposit_address(self, coin: str, network: str = None) -> Dict:
        """
        Abstract method for creating a deposit address.

        :param coin: The symbol of the cryptocurrency.
        :param network: The network for the deposit.
        :return: A dictionary with deposit address details.
        """
        pass

    @abstractmethod
    def create_withdraw_request(self, coin: str, address: str, amount: float,
                                network: Optional[str] = None, **kwargs) -> Dict:
        """
        Abstract method for creating a withdrawal request.
        Buda exchange: only for Lightning withdrawals
        Binance exchange: For any kind of cripto

        :param coin: The symbol of the cryptocurrency to withdraw (e.g., 'BTC').
        :param address: The destination address for the withdrawal.
        :param amount: The amount of cryptocurrency to withdraw.
        :param network: Optional, the network to use for withdrawal.
        :param kwargs: Additional optional parameters (withdrawOrderId, addressTag, etc.).
        :return: A dictionary containing the withdrawal request ID.
        """
        pass

    @abstractmethod
    def new_order(self, base_currency: str, quote_currency: str, side: str, order_type: str) -> Dict:
        """
        Create a new order on the exchange.

        :param base_currency: The base currency in of the trading pair (e.g., 'BTC' in 'BTCUSDT').
        :param quote_currency: The base currency in of the trading pair (e.g., 'USDT' in 'BTCUSDT').
        :param side: The side of the order (BUY or SELL), ENUMS varies from exchange to exchange.
        :param order_type: The type of the order (LIMIT, MARKET, STOP_LOSS, etc.).
        :return: The response from the exchange API as a dictionary.
        """
        pass

    @abstractmethod
    def cancel_order(self, base_currency: str, quote_currency: str, order_id: int) -> Dict:
        """
        Cancel an order on the exchange.

        :param base_currency: The base currency in of the trading pair (e.g., 'BTC' in 'BTCUSDT').
        :param quote_currency: The base currency in of the trading pair (e.g., 'USDT' in 'BTCUSDT').
        :param order_id: identification of the order to cancel.

        :return: The response from the exchange API as a dictionary.
        """

    @abstractmethod
    def get_price(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Get the order price of orders in a given market.

        :param base_currency: The base currency in of the trading pair (e.g., 'BTC' in 'BTCUSDT').
        :param quote_currency: The base currency in of the trading pair (e.g., 'USDT' in 'BTCUSDT').

        :return: The response from the exchange API as a dictionary.
        """

    @abstractmethod
    def _sign_request(self, params: Dict[str, str]) -> Dict[str, str]:
        """
        Sign the API request.

        :param params: Dictionary of query parameters.
        :return: Dictionary of signed query parameters.
        """

    @abstractmethod
    def create_quote_currency_address(self, coin: str, network: Optional[str] = None) -> Dict:
        """
        Create a deposit address for any available alt_coin.

        :param coin: The cryptocurrency symbol.
        :param network: The network for the deposit.
        """

    @abstractmethod
    def create_lightning_invoice(self, amount: float, **kwargs) -> Dict:
        """
        Create a lightning invoice for a given amount.

        :param amount: The amount to deposit (in BTC fractions).
        :param kwargs: Optional parameters, e.g., memo, expiry_seconds.
        :return: A dictionary containing the deposit address and related details.
        """

    @abstractmethod
    def pay_ln_invoice(self, ln_invoice: str, amount: float, **kwargs) -> Dict:
        """
        Submit a withdrawal request in Binance for BTC, via Lightning Network.

        :param ln_invoice: The destination address for the withdrawal (Lightning Network Invoice).
        :param amount: The withdrawal amount (in fractions of BTC).
        :param kwargs: Additional optional parameters.
        :return: A dictionary containing the withdrawal request ID.
        """