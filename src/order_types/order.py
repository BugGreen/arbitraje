from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class Order(ABC):
    """
    Abstract base class defining the interface and partial implementation
    for different kinds of Orders.

    Subclasses must implement:
      - _set_order_costs (or whichever method is needed to compute costs).
    """

    def __init__(self,
                 base_currency: str,
                 quote_currency: str,
                 amount: float,
                 price: Optional[float] = None,
                 status: str = 'pending',
                 trades: Optional[List[Dict]] = None,
                 order_type: Optional[str] = None):
        """
        :param base_currency: The base currency in the trading pair (e.g., 'btc' in 'btc-usd').
        :param quote_currency: The quote currency in the trading pair (e.g., 'usd' in 'btc-usd').
        :param amount: The total amount to be exchanged.
        :param price: The price of the asset (optional, required for limit orders).
        :param status: The status of the order ('pending', 'fulfilled', etc.). Defaults to 'pending'.
        :param trades: A list of trades (dictionaries) used to fulfill the order.
        :param order_type: The type of order (e.g., 'BUDA Bid Limit').
        """
        self.base_currency = base_currency.upper()
        self.quote_currency = quote_currency.upper()
        self.amount = amount
        self.price = price
        self.status = status
        self.trades = trades or []
        self.order_type = order_type

        self.variable_costs = 0.0
        self.fixed_costs = 0.0
        self.sub_orders: List[Dict[str, any]] = []  # Sub-orders created by strategies

        # Let the child class set the costs
        self._set_order_costs()

    @abstractmethod
    def _set_order_costs(self) -> None:
        """
        Abstract method to set the variable and fixed costs based on
        the specifics of the order type. Must be implemented by child classes.
        """
        pass

    def add_trade(self, trade: Dict) -> None:
        """
        Add a trade to the order (used for partial fulfillment).

        :param trade: A dictionary containing trade details (e.g., amount, price, exchange).
        """
        self.trades.append(trade)

    def is_fulfilled(self) -> bool:
        """
        Check if the order has been fulfilled based on the total amount of the trades.

        :return: True if the order is fulfilled, False otherwise.
        """
        total_fulfilled = sum(trade['amount'] for trade in self.trades)
        return total_fulfilled >= self.amount

    def get_remaining_amount(self) -> float:
        """
        Get the remaining amount of the order that still needs to be fulfilled.

        :return: The remaining amount to be fulfilled.
        """
        total_fulfilled = sum(trade['amount'] for trade in self.trades)
        return self.amount - total_fulfilled

    def get_total_cost(self) -> float:
        """
        Calculate the total cost of fulfilling the order, including variable and fixed costs.

        :return: The total cost of the order.
        """
        total_cost = self.amount * self.variable_costs + self.fixed_costs
        return total_cost

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"{self.base_currency}-{self.quote_currency}, "
                f"{self.amount} {self.quote_currency}, "
                f"status={self.status})")
