from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Any
from src.exchange_api.base_exchange import BaseExchange
import logging

logger = logging.getLogger(__name__)


class BaseLowLiquidityExchange(BaseExchange, ABC):
    """
    Abstract base class for low liquidity exchanges.
    Inherits all abstract methods from BaseExchange and may include additional methods
    specific to low liquidity trading environments.
    """

    @abstractmethod
    def batch_cancellation(self, orders: List[Dict]) -> Dict:
        """
        Cancel orders in batch on the exchange.

        :param orders: A list of orders to be canceled, where each order is a dictionary containing 'order_id' or 'client_id'.
        :return: The response from the exchange API indicating whether the batch cancelation was successful.
        """

    @abstractmethod
    def batch_creation(self, orders: List[Dict]) -> Dict:
        """
        Create new orders in batch on the exchange.

        :param orders: A list of orders to be created, where each order is a dictionary containing order details.
        :return: The response from the exchange API indicating whether the batch creation was successful.
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
    def get_order_book(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Retrieve the current order book for a specified market.

        :param base_currency: The base currency of the trading pair (e.g., 'BTC').
        :param quote_currency: The quote currency of the trading pair (e.g., 'USD').
        :return: A dictionary containing 'asks' and 'bids' lists from the order book.
        """
        pass

    @abstractmethod
    def _get_withdraw_or_deposit_history(self, coin: str, direction: str) -> Dict[str, List[Dict]]:
        """
        Get the Deposit/Withdrawal history of a given coin, or a given order.

        :param coin: Coin of interest
        :param direction: deposits/withdrawals
        :return: Deposit/Withdrawal history
        """

    @abstractmethod
    def get_market_info(self, base_currency: str, quote_currency: str) -> Dict:
        """
        Retrieve the market information of the market f'{base_currency}-{quote_currency}'.

        :param base_currency: The base currency of the trading pair (e.g., 'BTC').
        :param quote_currency: The quote currency of the trading pair (e.g., 'USDC').
        :return: A dictionary containing the market information.
        """

    @abstractmethod
    def _translate_batch_response(response: Union[Dict[str, Any], Exception]) \
            -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Translate the low liquidity exchange response into a standardized format.

        :param response: The raw response from the exchange or an Exception.
        :return: Standardized response.
        """