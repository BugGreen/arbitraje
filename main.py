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
    level=logging.WARNING,  # Set to DEBUG to capture all levels of log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('arbitrage_log.txt')  # Log file path
file_handler.setLevel(logging.DEBUG)  # Capture DEBUG level and above logs


def main() -> None:
    """
    Main function to run the arbitrage bot.
    """
    # Example usage with Binance

    try:

        welcome_menu()
        buda_proxy = BudaProxy()

        # Connect to the WebSocket for BTC/USDT market
        initial_order_book_ss = buda_proxy.get_order_book('BTC', 'clp')
        buda_proxy.connect_to_order_book('BTC', 'clp', initial_order_book_ss)
        # bot = ArbitrageBot(
        #     exchange_high_liquidity='binance',
        #     exchange_low_liquidity='buda',
        #     price_diff_threshold=0.4,
        #     mode='conservative',
        #     base_currency='BTC',
        #     quote_currency='USDC',
        # )
        # arb_order = ArbitrageOrder(
        #     base_currency="BTC",
        #     quote_currency="USDC",
        #     original_amount=20,
        #     currency_of_interest=CurrencyOfInterest.QUOTE,
        #     order_type=OrderType.SELL_LIMIT
        # )
        # arb_order2 = ArbitrageOrder(
        #     base_currency="BTC",
        #     quote_currency="USDC",
        #     original_amount=20,
        #     currency_of_interest=CurrencyOfInterest.QUOTE,
        #     order_type=OrderType.BUY_LIMIT
        # )
        # bot.run_arbitrage_flow(arb_orders=[arb_order, arb_order2])

        binance: BinanceProxy = ExchangeFactory.get_exchange("binance")
        coin = "USDC"
        ln_invoice = 'lnbc50u1pn5f8ljpp5dc6y936p79j9dfqs59vdkz6dfurxcgzvsren4mtahdrva9paqxhsdq8w3jhxaqcqzzsxqyz5vqsp5yp9j2fghxfw4dvxnkcu5lyldykew7ymuq27f8jpay8ms7q9kwe9s9qxpqysgqqczpcedj6ry8t8z5emqvz9mvjr263fsv7p64st6j5pyxfcdmm9hparffkgfsxv883kh6hkczfgpktlevn3rldcskqv392fk8n7ad3lcp6yx88t'
        sats_amount = 5000
        fiat_amount_usdc = 10
        base_currency, quote_currency = 'btc', 'usdc'
        price = 98000
        order_amount = str(round(fiat_amount_usdc / price, 5))
        #print(order_amount)
        side = 'BUY'
        time_in_force = 'GTC'
        order_type = 'MARKET'
        order_id = 33188802974


    except Exception as e:
        print(f"Error with Binance: {e}")

    # Example usage with BUDA
    try:
        buda: BudaProxy = ExchangeFactory.get_exchange("buda")
        coin = "BTC"
        base_currency, quote_currency = 'BTC', 'USDC'
        side = 'bid'
        order_type = 'limit'
        order_amount = 0.0012
        price = 15000000
        order_id = 1267767109

        orders = [
            {"mode": "place",
             "order": {"amount": 0.00100000012, "limit": 10000000, "market_name": "eth-cop", "price_type": "limit",
                       "type": "Bid"}},
            {"mode": "place",
             "order": {"amount": 0.0012, "limit": 10000000, "market_name": "eth-cop", "price_type": "limit",
                       "type": "Bid"}},
        ]
        order_to_cancel = [
            {"mode": "cancel", "order_id": 1309924955},
            {"mode": "cancel", "order_id": 1309924956},
            {"mode": "cancel", "order_id": 1318255904},
            {"mode": "cancel", "order_id": 1318255905},

        ]

        ltc_address = "LeMNHpnvULWbh9wHqNPdPwnip3vnSsXATY"

    except Exception as e:
        print(f"Error with BUDA: {e}")


def json_print(json_dict: json, indent: int = 2) -> None:
    print(json.dumps(json_dict, indent=indent))


if __name__ == "__main__":
    main()

