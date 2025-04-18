from src.order_types.order import Order
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class ArbitrageOrder(Order):
    def __init__(
        self,
        base_currency: str,
        quote_currency: str,
        amount: float,
        price: Optional[float] = None,
        status: str = 'pending',
        trades: Optional[List[Dict]] = None,
        order_type: Optional[str] = None,
        original_amount: float = 0.0
    ):
        super().__init__(base_currency, quote_currency, amount, price, status, trades, order_type)

        # The original total amount we aim to arbitrage
        self.original_amount = original_amount or amount
        # dynamic attributes for low-liquidity side
        self.traded_amount_low_liquidity = 0.0
        self.pending_amount_low_liquidity = self.original_amount  # Initially the entire original amount is pending
        # TODO: Se puede adicionar otro atributo que guarde lo que se tradeo en fiat, usando la respuesta
        # TODO: de get_order_states con la llave "exchanged_amount"
        # Potential future logic for high-liquidity side if needed
        # self.traded_amount_high_liquidity = 0.0
        # self.pending_amount_high_liquidity = self.original_amount
        # Dynamic tracking of how much we traded on each exchange
        self.traded_amount_high_liquidity = 0.0

    def update_low_liquidity_traded(self, traded_delta: float) -> None:
        """
        Add the traded_delta to the 'traded_amount_low_liquidity'.
        Could be called after each partial fill or sub-order fill on the low-liquidity exchange.
        """
        self.traded_amount_low_liquidity += traded_delta

    def update_high_liquidity_traded(self, traded_delta: float) -> None:
        """
        Same logic, for the high-liquidity side of the trade.
        """
        self.traded_amount_high_liquidity += traded_delta

    def both_sides_traded_enough(self, threshold: float = 0.001) -> bool:
        """
        Check if both traded_amount_low_liquidity and traded_amount_high_liquidity
        are close (within `threshold`) to the original_amount.
        """
        # Example criterion: each side is at least (original_amount - threshold)
        if (abs(self.traded_amount_low_liquidity - self.original_amount) <= threshold and
            abs(self.traded_amount_high_liquidity - self.original_amount) <= threshold):
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
