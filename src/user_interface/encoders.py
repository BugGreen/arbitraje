from typing import Dict, Any, List
from enum import Enum
from src.order_types.encoders import OrderType, CurrencyOfInterest

from src.order_types.encoders import Profit, OrderType, CurrencyOfInterest, PROFIT_ROUNDING_DECIMALS


possible_sides: List[str] = ["ONE_SIDE", "BOTH_SIDES"]


arb_oder_sell_limit_values: Dict[str, Any] = {
    "Amount": 20,
    "Currency of Interest": "QUOTE",
    "Order Type": "SELL_LIMIT"
}

arb_oder_buy_limit_values: Dict[str, Any] = {
    "Amount": 20,
    "Currency of Interest": "QUOTE",
    "Order Type": "BUY_LIMIT"
}

arb_orders_values: Dict[str, Dict[str, Any]] = {
    "SELL_LIMIT": arb_oder_sell_limit_values,
    "BUY_LIMIT": arb_oder_buy_limit_values
}

market_values: Dict[str, Any] = {
    "Market": "BTC-USDC",
    "E. High Liquidity": 'binance',
    "E. Low Liquidity": 'buda',
    "P. Difference": 0.4,
    "Mode": possible_sides[0],
    "Side": "SELL_LIMIT"
}

print(arb_oder_sell_limit_values)