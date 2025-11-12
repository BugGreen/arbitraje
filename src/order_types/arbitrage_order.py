from src.order_types.order import Order
import logging
from typing import Optional, List, Dict, Callable
from src.order_types.encoders import Profit, OrderType, CurrencyOfInterest

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

    def update_profit(self, delta_amount_base_currency: float, delta_amount_quote_currency: float) -> None:
        """
        Calculates the profit based on the order type and the amount of interest.
        WARNING: ALWAYS use after `fulfill_high_liquidity` method.
        NOTE: An order can be either profitable or non-profitable, therefore attribute `profit` might have neg values

        :param delta_amount_base_currency: amount delta resulting from the desired BASE currency amount to trade and the
        actual amount traded.
        :param delta_amount_quote_currency: price delta resulting from the desired QUOTE currency amount to trade and the
        actual amount traded.
        """
        pending_quote_amount = self._pending_quote_amount_high_liquidity
        pending_base_amount = self._pending_base_amount_high_liquidity
        total_fees_base_currency = \
            self.paid_fee_base_currency_low_liquidity + self.paid_fee_base_currency_high_liquidity
        total_fees_quote_currency = \
            self.paid_fee_quote_currency_low_liquidity + self.paid_fee_quote_currency_high_liquidity

        if self.order_type == OrderType.BUY_LIMIT:
            if self.currency_of_interest == CurrencyOfInterest.QUOTE:
                self.profit = Profit(round(self.profit.amount - pending_quote_amount - total_fees_quote_currency, 7),
                                     self.quote_currency)

            elif self.currency_of_interest == CurrencyOfInterest.BASE:
                self.profit = Profit(round(self.profit.amount + pending_base_amount - total_fees_base_currency, 7),
                                     self.base_currency)

            self._pending_quote_amount_high_liquidity, self._pending_base_amount_high_liquidity = 0, 0

        elif self.order_type == OrderType.SELL_LIMIT:
            if self.currency_of_interest == CurrencyOfInterest.QUOTE:
                self.profit = Profit(round(self.profit.amount + pending_quote_amount - total_fees_quote_currency, 7),
                                     self.quote_currency)

            elif self.currency_of_interest == CurrencyOfInterest.BASE:
                self.profit = Profit(round(self.profit.amount - pending_base_amount - total_fees_base_currency, 7),
                                     self.base_currency)

            self._pending_base_amount_high_liquidity = delta_amount_base_currency
            self._pending_quote_amount_high_liquidity = delta_amount_quote_currency

        else:
            logger.warning(f"No logic for order_type: {self.order_type}")

        # TODO: Extend to SELL_MARKET and BUY _MARKET

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
