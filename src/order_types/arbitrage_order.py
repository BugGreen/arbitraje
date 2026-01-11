from src.order_types.order import Order
import logging
from typing import Optional, List, Dict, Callable
from src.order_types.encoders import Profit, OrderType, CurrencyOfInterest, PROFIT_ROUNDING_DECIMALS

logger = logging.getLogger(__name__)


class ArbitrageOrder(Order):
    def __init__(
        self,
        base_currency: str,
        quote_currency: str,
        amount: float,
        currency_of_interest: CurrencyOfInterest,
        order_type: OrderType,
        price: Optional[float] = None,
        status: str = 'pending',
        trades: Optional[List[Dict]] = None,
        original_amount: float = 0.0,
    ):
        super().__init__(base_currency, quote_currency, amount, price, status, trades, order_type)

        # The original total amount we aim to arbitrage
        self.original_amount = original_amount or amount

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

        # Defines the currency to accumulate base or quote (e.g. BTCUSDC, base=BTC)
        self.currency_of_interest = currency_of_interest

        self.order_type = order_type

        if self.currency_of_interest == CurrencyOfInterest.QUOTE:
            self.profit = Profit(0, self.quote_currency)
        if self.currency_of_interest == CurrencyOfInterest.BASE:
            self.profit = Profit(0, self.base_currency)

        # Optionally, define a callback that gets invoked whenever pending_amount_high_liquidity changes.
        # e.g. def on_pending_high_liquidity_update(arb_order, delta): ...
        self.on_pending_high_liquidity_updated: Optional[Callable[['ArbitrageOrder', float], None]] = None

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

        if self.on_pending_high_liquidity_updated is not None:
            self.on_pending_high_liquidity_updated(self, traded_quote_delta)

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
