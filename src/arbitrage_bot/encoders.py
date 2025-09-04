from typing import Dict, List

MIN_BTC_PER_INVOICE: str = 0.000019
MAX_BTC_PER_INVOICE: str = 0.00995

MIN_AMOUNT_REQUIREMENTS: Dict[str, float] = {
    "BTC-CLP": 0.00002,
    "BTC-COP": 0.00002,
    "ETH-CLP": 0.001,
    "ETH-BTC": 0.001,
    "BTC-PEN": 0.00002,
    "ETH-PEN": 0.001,
    "ETH-COP": 0.001,
    "BCH-BTC": 0.001,
    "BCH-CLP": 0.001,
    "BCH-COP": 0.001,
    "BCH-PEN": 0.001,
    "LTC-BTC": 0.003,
    "LTC-CLP": 0.003,
    "LTC-COP": 0.003,
    "LTC-PEN": 0.003,
    "USDC-CLP": 0.01,
    "USDC-COP": 0.01,
    "USDC-PEN": 0.01,
    "BTC-USDC": 0.00002,
    "USDT-USDC": 0.01
}

MIN_AMOUNT_BINANCE_REQUIREMENTS: Dict[str, int] = {
    "BTCUSDC": 10,
}

# TODO: Rellenar esta lista de manera automatica
MIN_WITHDRAWAL_AMOUNT_BINANCE: Dict[str, int] = {
    "USDC": 20
}

# The distributed amount according to the number of desired sub_orders
AMOUNT_DISTRIBUTION_SUB_ORDERS: Dict[int, List[float]] = {
    1: [1.0],
    2: [0.8, 0.2],
    3: [0.6, 0.3, 0.1]
}