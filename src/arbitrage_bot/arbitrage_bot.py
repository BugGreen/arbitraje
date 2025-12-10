from typing import Optional, Type, Dict
from src.exchange_api.exchange_factory import ExchangeFactory
from src.arbitrage_bot.order import Order
from src.exchange_api.binance_proxy import BinanceProxy
from src.exchange_api.buda_proxy import BudaProxy


class ArbitrageBot:
    def __init__(self, exchange_a: str, exchange_b: str, price_difference: float,
                 base_currency: str, quote_currency: str, amount: float, mode: Optional[str] = 'conservative'):
        """
        Initializes the arbitrage bot with the specified exchanges, price difference threshold,
        and mode for order execution.

        :param exchange_a: The first exchange for arbitrage (e.g., 'binance', 'buda').
        :param exchange_b: The second exchange for arbitrage.
        :param price_difference: The minimum price difference (in percentage) to trigger arbitrage.
        :param mode: The mode of operation for the bot (e.g., 'aggressive', 'conservative').
        :param base_currency: The base currency of the trading pair (e.g., 'btc').
        :param quote_currency: The quote currency of the trading pair (e.g., 'usd').
        :param amount: The total amount to be traded for arbitrage.
        """
        self.exchange_a = exchange_a
        self.exchange_b = exchange_b
        self.price_difference = price_difference
        self.mode = mode
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.amount = amount
        self.exchange_a_instance = self._create_exchange(exchange_a)
        self.exchange_b_instance = self._create_exchange(exchange_b)

    @staticmethod
    def _create_exchange(exchange_name: str) -> Type[BinanceProxy or BudaProxy]:
        """
        Factory method to create exchange instances based on the exchange name.

        :param exchange_name: The name of the exchange (e.g., 'binance', 'buda').
        :return: The exchange class instance.
        :raises ValueError: If an unsupported exchange is provided.
        """
        factory = ExchangeFactory()
        return ExchangeFactory.get_exchange(exchange_name)

    def get_price_difference(self) -> float:
        """
        Calculates the price difference between the two exchanges in percentage.

        :return: The price difference in percentage.
        """
        price_a = self.exchange_a_instance.get_price(self.base_currency, self.quote_currency)
        price_b = self.exchange_b_instance.get_price(self.base_currency, self.quote_currency)

        price_diff = abs(price_a - price_b) / min(price_a, price_b) * 100
        return price_diff

    def execute_arbitrage(self) -> Dict:
        """
        Executes the arbitrage strategy if the price difference between the two exchanges exceeds
        the defined threshold. The bot will place orders on both exchanges accordingly.

        :return: A dictionary with the result of the arbitrage execution.
        """
        price_diff = self.get_price_difference()
        if price_diff < self.price_difference:
            return {"status": "no arbitrage", "price_diff": price_diff}

        # Decide whether to place limit or market orders based on the mode
        if self.mode == 'aggressive':
            order_type = 'market'
        elif self.mode == 'conservative':
            order_type = 'limit'
        else:
            raise ValueError("Unsupported mode. Use 'aggressive' or 'conservative'.")

        # Create and place orders
        order_a = Order(self.base_currency, self.quote_currency, self.amount / 2, order_type=order_type)
        order_b = Order(self.base_currency, self.quote_currency, self.amount / 2, order_type=order_type)

        # Place orders on both exchanges
        order_a_response = self.exchange_a_instance.new_order(order_a)
        order_b_response = self.exchange_b_instance.new_order(order_b)

        return {
            "status": "arbitrage executed",
            "order_a": order_a_response,
            "order_b": order_b_response,
            "price_diff": price_diff
        }
