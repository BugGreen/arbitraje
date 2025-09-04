from src.order_types.encoders import Profit, OrderType, CurrencyOfInterest, PROFIT_ROUNDING_DECIMALS
from typing import Optional, List, Dict, Callable, Any
from src.order_types.order import Order
import logging

logger = logging.getLogger(__name__)


class ArbitrageOrder(Order):
    def __init__(
        self,
        base_currency: str,
        quote_currency: str,
        currency_of_interest: CurrencyOfInterest,
        order_type: OrderType,
        original_amount: float = 0.0,
        low_liquidity_exchange: str = "BUDA",
        high_liquidity_exchange: str = "BINANCE",
        sub_orders_num: int = 3
    ):
        super().__init__(base_currency=base_currency, quote_currency=quote_currency, order_type=order_type)
        # GLOBAL ATTRIBUTES ------------------------------------------
        # The original total amount we aim to arbitrage
        self.original_amount = original_amount
        # Defines the currency to accumulate base or quote (e.g. BTCUSDC, base=BTC)
        self.currency_of_interest = currency_of_interest
        self.order_type = order_type
        self.sub_orders_num = sub_orders_num  # Number of sub-orders to create

        # DYNAMIC ATTRIBUTES ------------------------------------------
        # Dynamic attributes Low-liquidity side
        self.pending_amount_low_liquidity = self.original_amount  # Initially the entire original amount is pending
        self.traded_base_amount_low_liquidity: float = 0.0
        self.traded_quote_amount_low_liquidity: float = 0.0
        self.paid_fee_base_currency_low_liquidity: float = 0.0
        self.paid_fee_quote_currency_low_liquidity: float = 0.0
        # This is how much has actually been traded (sub-orders filled) on the low-liquidity exchange

        # High-liquidity side
        self.traded_amount_base_high_liquidity: float = 0.0
        self.traded_amount_quote_high_liquidity: float = 0.0
        self.paid_fee_base_currency_high_liquidity: float = 0.0
        self.paid_fee_quote_currency_high_liquidity: float = 0.0

        # This accumulates how much has actually been executed on the high-liquidity side

        # This is the portion that is "ready to be offset" on the high-liquidity side
        # after it was successfully traded on the low-liquidity side:
        self._pending_quote_amount_high_liquidity: float = 0.0
        self._pending_base_amount_high_liquidity: float = 0.0

        if self.currency_of_interest == CurrencyOfInterest.QUOTE:
            self.profit = Profit(0, self.quote_currency)
        if self.currency_of_interest == CurrencyOfInterest.BASE:
            self.profit = Profit(0, self.base_currency)

        self.price_difference: float = 0
        self.low_liquidity_price: float = 0
        self.high_liquidity_price: float = 0
        self.low_liquidity_exchange: str = low_liquidity_exchange
        self.high_liquidity_exchange: str = high_liquidity_exchange

        self.price_reference = None  # Store price reference here
        self.sub_orders_info = None  # Info about the sub_orders that conforms the amount to trade
        self.sub_orders_ids: List[str] = []
        self.order_completed: bool = False
        self.order_number: int = 1  # The number of the current order (Add one when completed)

    def update_sub_orders_info(self, sub_orders_info: dict):
        """
        Update the price reference.
        WARNING: This is not the order price, but the reference price to place the order.

        :param sub_orders_info: dict containing the sub orders info related to this order.
        """
        self.sub_orders_info = sub_orders_info  # Update it when necessary

    def update_price_reference(self, price_reference: float):
        """
        Update the price reference.
        WARNING: This is not the order price, but the reference price to place the order.

        :param price_reference: float representing the price used as a reference to calculate the real price to place
        an order.
        """
        self.price_reference = price_reference  # Update it when necessary

    def get_arbitrage_order_info(self) -> dict:
        arbitrage_order_info = {
            "original_amount": self.original_amount,
            "pending_amount_low_liquidity": self.pending_amount_low_liquidity,
            "traded_base_amount_low_liquidity": self.traded_base_amount_low_liquidity,
            "traded_quote_amount_low_liquidity": self.traded_quote_amount_low_liquidity,
            "pending_quote_amount_high_liquidity": self._pending_quote_amount_high_liquidity,
            "pending_base_amount_high_liquidity": self._pending_base_amount_high_liquidity,
            "traded_amount_base_high_liquidity": self.traded_amount_base_high_liquidity,
            "traded_amount_quote_high_liquidity": self.traded_amount_quote_high_liquidity
        }
        return arbitrage_order_info

    def update_low_liquidity_traded(self,
                                    traded_quote_delta: float,
                                    traded_base_delta: float,
                                    paid_fee_base_currency: float,
                                    paid_fee_quote_currency: float
                                    ) -> None:
        """
        Called whenever a sub-order on the low-liquidity exchange is traded or partially traded.

        Add traded_quote_delta to self.traded_amount_low_liquidity,
        and also set the same traded_quote_delta to `_pending_quote_amount_high_liquidity`,
        and set  traded_base_delta to `_pending_base_amount_high_liquidity`.
        meaning that exact portion is now ready to be offset on the high-liquidity side.

        :param traded_base_delta: The traded amount expressed in the base currency
        :param traded_quote_delta: The traded amount expressed in the quote currency
        :param paid_fee_base_currency: The paid fee expressed in the base currency
        :param paid_fee_quote_currency: The paid fee expressed in the quote currency
        """
        self.traded_base_amount_low_liquidity += traded_base_delta
        self.traded_quote_amount_low_liquidity += traded_quote_delta
        self.pending_amount_low_liquidity -= traded_quote_delta
        self.paid_fee_base_currency_low_liquidity += paid_fee_base_currency
        self.paid_fee_quote_currency_low_liquidity += paid_fee_quote_currency
        # Move that same traded_delta to pending
        self._pending_quote_amount_high_liquidity += traded_quote_delta
        self._pending_base_amount_high_liquidity += traded_base_delta

    def update_market_data(self,
                           price_diff: float,
                           low_liquidity_price: float,
                           high_liquidity_price: float
                           ) -> None:
        """
        Tracks market data by updating attributes `price_difference`, `low_liquidity_price` and `high_liquidity_price`

        :param price_diff: The price difference between exchanges as a decimal fraction. For example, 0.05 means 5%.
        :param low_liquidity_price: The asset price on the low-liquidity exchange (float)
        :param high_liquidity_price: The asset price on the high-liquidity exchange (float)
        """
        self.price_difference = price_diff
        self.low_liquidity_price = low_liquidity_price
        self.high_liquidity_price = high_liquidity_price

    @property
    def get_pending_quote_amount_high_liquidity(self):
        return self._pending_quote_amount_high_liquidity

    @property
    def get_pending_base_amount_high_liquidity(self):
        return self._pending_base_amount_high_liquidity

    def reset_values(self, order_completion: bool) -> None:
        """
        Restore all trading values, except `_pending_quote_amount_high_liquidity` and
        `_pending_base_amount_high_liquidity`, because these can be used in the next order
        (in case there is an amount left to execute).
        :param order_completion: True if the order was successfully completed, else False
        :return: None
        """
        if order_completion:
            # Global attributes
            self.order_number += 1  # Star a new order
            self.sub_orders_info: List = []
            self.sub_orders_ids: List = []
            self.order_completed: bool = False
            # Dynamic attributes Low-liquidity side
            self.pending_amount_low_liquidity = self.original_amount  # Initially the entire original amount is pending
            self.traded_base_amount_low_liquidity: float = 0.0
            self.traded_quote_amount_low_liquidity: float = 0.0
            self.paid_fee_base_currency_low_liquidity: float = 0.0
            self.paid_fee_quote_currency_low_liquidity: float = 0.0
            # This is how much has actually been traded (sub-orders filled) on the low-liquidity exchange

            # High-liquidity side
            self.traded_amount_base_high_liquidity: float = 0.0
            self.traded_amount_quote_high_liquidity: float = 0.0
            self.paid_fee_base_currency_low_liquidity: float = 0.0
            self.paid_fee_quote_currency_high_liquidity: float = 0.0

            if self.currency_of_interest == CurrencyOfInterest.QUOTE:
                self.profit = Profit(0, self.quote_currency)
            if self.currency_of_interest == CurrencyOfInterest.BASE:
                self.profit = Profit(0, self.base_currency)

    def fulfill_high_liquidity(self,
                               traded_quote_delta: float,
                               traded_base_delta: float,
                               paid_fee_base_currency: float,
                               paid_fee_quote_currency: float) -> None:
        """
        Called after the high-liquidity side is traded. We reduce the pending amounts (expressed in quote and base
        currencies) by 'traded_quote_delta' and "traded_base_delta'.
        Then increase self.traded_amount_high_liquidity by the same.

        :param traded_base_delta: The traded amount expressed in the base currency
        :param traded_quote_delta: The traded amount expressed in the quote currency
        :param paid_fee_base_currency: The paid fee expressed in the base currency
        :param paid_fee_quote_currency: The paid fee expressed in the quote currency
        """
        # Suppose we do not allow partial pending to remain.
        # But if partial is possible, you'd do a min operation
        self._pending_quote_amount_high_liquidity -= traded_quote_delta
        self._pending_base_amount_high_liquidity -= traded_base_delta

        self.traded_amount_base_high_liquidity += traded_base_delta
        self.traded_amount_quote_high_liquidity += traded_quote_delta

        self.paid_fee_base_currency_high_liquidity += paid_fee_base_currency
        self.paid_fee_quote_currency_high_liquidity += paid_fee_quote_currency

    def update_profit(self, price_difference: float) -> None:
        """
        Calculates the profit based on the order type and the amount of interest, including fees.

        WARNING: ALWAYS use after `fulfill_high_liquidity` method.
        NOTE: An order can be either profitable or non-profitable, therefore the `profit` attribute may have negative values.

        :param price_difference: The real price difference between the low and high liquidity exchanges.
        """
        currency_of_interest = self.currency_of_interest
        order_type = self.order_type

        # Total paid fees for both base and quote currencies across both exchanges
        total_fees_base_currency = self.paid_fee_base_currency_low_liquidity + self.paid_fee_base_currency_high_liquidity
        total_fees_quote_currency = self.paid_fee_quote_currency_low_liquidity + self.paid_fee_quote_currency_high_liquidity

        # Calculate the percentage of executed amount
        base_amount_traded_percentage = abs(
            self.traded_amount_base_high_liquidity / self.traded_base_amount_low_liquidity)
        quote_amount_traded_percentage = abs(
            self.traded_amount_quote_high_liquidity / self.traded_quote_amount_low_liquidity)

        # Compute profit based on the currency of interest
        if currency_of_interest == CurrencyOfInterest.QUOTE:
            profit_quote_amount = self._calculate_profit_quote(order_type, price_difference,
                                                               base_amount_traded_percentage,
                                                               quote_amount_traded_percentage)
            self.profit = Profit(round(profit_quote_amount - total_fees_quote_currency, PROFIT_ROUNDING_DECIMALS),
                                 self.quote_currency)
        elif currency_of_interest == CurrencyOfInterest.BASE:
            profit_base_amount = self._calculate_profit_base(order_type, price_difference,
                                                             base_amount_traded_percentage,
                                                             quote_amount_traded_percentage)
            self.profit = Profit(round(profit_base_amount - total_fees_base_currency, PROFIT_ROUNDING_DECIMALS),
                                 self.base_currency)
        else:
            logger.warning(f"No logic for order_type: {self.order_type}")

    def _calculate_profit_quote(self, order_type: 'OrderType', price_difference: float,
                                base_amount_traded_percentage: float, quote_amount_traded_percentage: float) -> float:
        """
        Helper method to calculate profit in quote currency.
        :param order_type: The type of the order (BUY/SELL).
        :param price_difference: The price difference in decimal form (e.g., 0.05 = 5%).
        :param base_amount_traded_percentage: The percentage of the base currency traded.
        :param quote_amount_traded_percentage: The percentage of the quote currency traded.
        :return: The calculated profit in quote currency.
        """
        if order_type in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            profit = base_amount_traded_percentage * self.traded_quote_amount_low_liquidity * price_difference
            self._pending_quote_amount_high_liquidity = 0
        elif order_type in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            profit = quote_amount_traded_percentage * self.traded_quote_amount_low_liquidity * price_difference
            self._pending_base_amount_high_liquidity = 0
        return profit

    def _calculate_profit_base(self, order_type: 'OrderType', price_difference: float,
                               base_amount_traded_percentage: float, quote_amount_traded_percentage: float) -> float:
        """
        Helper method to calculate profit in base currency.
        :param order_type: The type of the order (BUY/SELL).
        :param price_difference: The price difference in decimal form (e.g., 0.05 = 5%).
        :param base_amount_traded_percentage: The percentage of the base currency traded.
        :param quote_amount_traded_percentage: The percentage of the quote currency traded.
        :return: The calculated profit in base currency.
        """
        if order_type in [OrderType.BUY_LIMIT, OrderType.BUY_MARKET]:
            profit = base_amount_traded_percentage * self.traded_base_amount_low_liquidity * price_difference
            self._pending_quote_amount_high_liquidity = 0
        elif order_type in [OrderType.SELL_LIMIT, OrderType.SELL_MARKET]:
            profit = quote_amount_traded_percentage * self.traded_base_amount_low_liquidity * price_difference
            self._pending_base_amount_high_liquidity = 0
        return profit

    def update_high_liquidity_traded(self, traded_delta: float) -> None:
        """
        Same logic, for the high-liquidity side of the trade.
        """
        self.traded_amount_quote_high_liquidity += traded_delta

    def both_sides_traded_enough(self, threshold: float = 0.001) -> bool:
        """
        Check if both traded_amount_low_liquidity and traded_amount_high_liquidity
        are close (within `threshold`) to the original_amount.
        """
        # Example criterion: each side is at least (original_amount - threshold)
        if (abs(self.traded_quote_amount_low_liquidity - self.original_amount) <= threshold and
            abs(self.traded_amount_quote_high_liquidity - self.original_amount) <= threshold):
            return True
        return False

    def _set_order_costs(self) -> None:
        """
        Buda-specific cost logic.
        """
        # ToDo: Actualizar los datos:

        if self.order_type == 'BUDA_bid_limit':
            self.variable_costs = 0.1 / 100
            self.fixed_costs = 6
        elif self.order_type == 'BUDA_bid_market':
            self.variable_costs = 0.8 / 100
            self.fixed_costs = 6
        elif self.order_type == 'BUDA_ask_limit':
            self.variable_costs = 0.1 / 100
            self.fixed_costs = 7.1
        elif self.order_type == 'BUDA_ask_market':
            self.variable_costs = 0.8 / 100
            self.fixed_costs = 7.1
        else:
            self.variable_costs = 0.0
            self.fixed_costs = 0.0
