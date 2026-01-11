from collections import namedtuple
from enum import Enum

Profit = namedtuple('Profit', 'amount, currency')  # Point has members `amount` and `currency`

PROFIT_ROUNDING_DECIMALS = 7


class OrderType(Enum):
    BUY_LIMIT = 0  # Limit order (buy) in low_liquidity exchange, market order (sell) in high_liquidity exchange
    SELL_LIMIT = 1  # Market order (buy) in low_liquidity exchange, market order (sell) in high_liquidity exchange
    BUY_MARKET = 2  # Limit order (sell) in low_liquidity exchange, market order (buy) in high_liquidity exchange
    SELL_MARKET = 4  # Market order (sell) in low_liquidity exchange, market order (buy) in high_liquidity exchange


class CurrencyOfInterest(Enum):
    """
    Defines the currency to accumulate base or quote (e.g. For market BTCUSDC, BASE=BTC, QUOTE=USDC)
    """
    QUOTE = 0
    BASE = 1

