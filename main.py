from src.arbitrage_bot.arbitrage_bot import ArbitrageBot
from src.exchange_api.high_liquidity_exchanges.binance_proxy import BinanceProxy
from src.exchange_api.low_liquidity_exchanges.buda_proxy import BudaProxy
from src.exchange_api.exchange_factory import ExchangeFactory
from src.order_types.arbitrage_order import ArbitrageOrder
from src.order_types.encoders import CurrencyOfInterest, OrderType
from src.telegram_bot.telegram_alert import TelegramAlert
from src.user_interface.arbitrage_ui import welcome_menu
import asyncio
import logging
import json


logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all levels of log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('arbitrage_log.txt')  # Log file path
file_handler.setLevel(logging.DEBUG)  # Capture DEBUG level and above logs


def main() -> None:
    """
    Main function to run the arbitrage bot.
    """
    try:
        welcome_menu()
    except Exception as e:
        print(f"[main.py] -- Error with ArbitrageBot creation: {e}")


def json_print(json_dict: json, indent: int = 2) -> None:
    print(json.dumps(json_dict, indent=indent))


if __name__ == "__main__":
    main()

