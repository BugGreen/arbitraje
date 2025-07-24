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
        pass
