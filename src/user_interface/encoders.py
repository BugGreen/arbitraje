from typing import Dict, Any
from src.order_types.encoders import Profit, OrderType, CurrencyOfInterest, PROFIT_ROUNDING_DECIMALS

initialization_values: Dict[str, Any] = {
    "E. High Liquidity": 'binance',
    "E. Low Liquidity": 'buda',
    "P. Difference": 0.4,
    "Base Currency": "BTC",
    "Quote Currency": "USDC",
    "Amount": 2000,
    "Mode": "debug"
}