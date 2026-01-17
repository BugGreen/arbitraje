from typing import Optional, Dict, Any


class ArbitrageOrder:
    def __init__(self,
                 base_currency: str,
                 quote_currency: str,
                 order_type: str,
                 total_amount: float,
                 price_reference: Optional[float] = None,
                 bid_order_id: Optional[int] = None,
                 ask_order_id: Optional[int] = None) -> None:
        """
        Initializes the ArbitrageOrder object, which tracks an arbitrage opportunity's details,
        including the bid/ask orders and the reference price for the trade.

        :param base_currency: The base currency for the trade (e.g., 'BTC').
        :param quote_currency: The quote currency for the trade (e.g., 'USDT').
        :param order_type: The type of order (e.g., 'BUY_LIMIT', 'SELL_LIMIT').
        :param total_amount: The total amount to be traded.
        :param price_reference: The reference price used to calculate the arbitrage opportunity.
        :param bid_order_id: The ID for the bid order.
        :param ask_order_id: The ID for the ask order.
        """
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.order_type = order_type
        self.total_amount = total_amount
        self.price_reference = price_reference
        self.bid_order_id = bid_order_id
        self.ask_order_id = ask_order_id
        self.filled_amount = 0.0
        self.pending_amount = total_amount

    def update_bid_order_id(self, order_information: Dict[str, Any]) -> None:
        """
        Updates the bid order ID based on the given order information.

        :param order_information: The order information containing the bid order ID.
        """
        self.bid_order_id = order_information.get('id', self.bid_order_id)

    def update_ask_order_id(self, order_information: Dict[str, Any]) -> None:
        """
        Updates the ask order ID based on the given order information.

        :param order_information: The order information containing the ask order ID.
        """
        self.ask_order_id = order_information.get('id', self.ask_order_id)

    def update_market_data(self, price_diff: float, low_liquidity_price: float, high_liquidity_price: float) -> None:
        """
        Updates the market data for the arbitrage order, including the price difference
        and the prices from the low- and high-liquidity exchanges.

        :param price_diff: The price difference between the two exchanges.
        :param low_liquidity_price: The price from the low-liquidity exchange.
        :param high_liquidity_price: The price from the high-liquidity exchange.
        """
        self.price_diff = price_diff
        self.low_liquidity_price = low_liquidity_price
        self.high_liquidity_price = high_liquidity_price

    def fulfill_order(self, filled_amount: float, price: float) -> None:
        """
        Marks the order as fulfilled for the given amount and price.

        :param filled_amount: The amount that was filled in the order.
        :param price: The price at which the order was filled.
        """
        self.filled_amount += filled_amount
        self.pending_amount -= filled_amount

    def is_fulfilled(self) -> bool:
        """
        Checks if the order is fully fulfilled.

        :return: True if the order is fully filled, False otherwise.
        """
        return self.pending_amount <= 0.0

    def reset_values(self, order_completion: bool = False) -> None:
        """
        Resets the order's state, useful for starting a new cycle or after completing the order.

        :param order_completion: A flag indicating if the order is completed. If True, reset the order.
        """
        if order_completion:
            self.filled_amount = 0.0
            self.pending_amount = self.total_amount
        self.bid_order_id = None
        self.ask_order_id = None
        self.price_reference = None

    def __repr__(self) -> str:
        """
        Provides a string representation of the ArbitrageOrder object.

        :return: A string representing the arbitrage order.
        """
        return f"ArbitrageOrder(base_currency={self.base_currency}, quote_currency={self.quote_currency}, " \
               f"order_type={self.order_type}, total_amount={self.total_amount}, " \
               f"filled_amount={self.filled_amount}, pending_amount={self.pending_amount})"
