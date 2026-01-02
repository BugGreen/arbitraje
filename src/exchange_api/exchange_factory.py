from exchange_api.high_liquidity_exchanges.binance_proxy import BinanceProxy
from exchange_api.low_liquidity_exchanges.buda_proxy import BudaProxy
from typing import Any


class ExchangeFactory:
    """
    Factory class to instantiate exchange proxies.
    """

    @staticmethod
    def get_exchange(exchange_name: str) -> Any:
        """
        Factory method to instantiate the appropriate exchange proxy based on the exchange name.

        :param exchange_name: Name of the exchange (e.g., 'binance', 'buda').
        :return: An instance of the corresponding exchange proxy.
        :raises ValueError: If the exchange is not supported.
        """
        exchange_name_lower = exchange_name.lower()
        if exchange_name_lower == "binance":
            return BinanceProxy()
        elif exchange_name_lower == "buda":
            return BudaProxy()
        else:
            raise ValueError(f"Exchange '{exchange_name}' is not supported.")
