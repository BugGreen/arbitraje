from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseExchange(ABC):
    """
    Abstract base class defining the interface for exchange proxies.
    """

    @abstractmethod
    def get_coin_info(self) -> List[Dict]:
        """
        Fetch information about all coins available for deposit and withdrawal.

        :return: A list of dictionaries containing coin information.
        """
        pass

    @abstractmethod
    def supports_lightning_network(self, coin: str) -> bool:
        """
        Check if the exchange supports the Lightning Network for a specific coin.

        :param coin: The symbol of the coin (e.g., 'BTC').
        :return: True if supported, False otherwise.
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
    def get_order_states(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Get the states of orders in a given market.

        :param base_currency: The base currency in of the trading pair (e.g., 'BTC' in 'BTCUSDT').
        :param quote_currency: The base currency in of the trading pair (e.g., 'USDT' in 'BTCUSDT').

        :return: The response from the exchange API as a dictionary.
        """

    @abstractmethod
    def batch_creation(self, orders: List[Dict]) -> Dict:
        """
        Create new orders in batch on the exchange.

        :param orders: A list of orders to be created, where each order is a dictionary containing order details.
        :return: The response from the exchange API indicating whether the batch creation was successful.
        """

    @abstractmethod
    def batch_cancellation(self, orders: List[Dict]) -> Dict:
        """
        Cancel orders in batch on the exchange.

        :param orders: A list of orders to be canceled, where each order is a dictionary containing 'order_id' or 'client_id'.
        :return: The response from the exchange API indicating whether the batch cancelation was successful.
        """