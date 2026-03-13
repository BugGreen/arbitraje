import json
from src.exchange_api.exchange_factory import ExchangeFactory
import requests
import logging

logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG to capture all levels of log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main function to run the arbitrage bot.
    """
    # Example usage with Binance
    try:
        binance = ExchangeFactory.get_exchange("binance")
        coin = "BTC"
        ln_invoice = 'lnbc50u1pn5f8ljpp5dc6y936p79j9dfqs59vdkz6dfurxcgzvsren4mtahdrva9paqxhsdq8w3jhxaqcqzzsxqyz5vqsp5yp9j2fghxfw4dvxnkcu5lyldykew7ymuq27f8jpay8ms7q9kwe9s9qxpqysgqqczpcedj6ry8t8z5emqvz9mvjr263fsv7p64st6j5pyxfcdmm9hparffkgfsxv883kh6hkczfgpktlevn3rldcskqv392fk8n7ad3lcp6yx88t'
        sats_amount = 5000
        order_amount = 0.00011
        base_currency, quote_currency = 'btc', 'usdt'
        price = 90000
        side = 'BUY'
        time_in_force = 'GTC'
        order_type = 'LIMIT'
        order_id = 33188802974

        #coin_info = binance.supports_lightning_network(coin)
        #withdraw_request = binance.create_withdraw_request(coin=coin, address=ln_invoice, amount=sats_amount)
        #print(json.dumps(withdraw_request, indent=2))
        #new_order = binance.new_order(base_currency=base_currency, quote_currency=quote_currency, side=side, order_type=order_type, price=price, quantity=order_amount, time_in_force=time_in_force)
        #print(json.dumps(new_order, indent=2))
        #cancel_order = binance.cancel_order(base_currency, quote_currency, order_id)
        #print(json.dumps(cancel_order, indent=2))
        #lightning_address = binance.create_deposit_address(coin)
        #print(json.dumps(lightning_address, indent=2))
        binance.check_datetime_differences()
        #print(json.dumps(coin_info, indent=2))
    except Exception as e:
        print(f"Error with Binance: {e}")

    # Example usage with BUDA
    try:
        buda = ExchangeFactory.get_exchange("buda")
        coin = "BTC"
        base_currency, quote_currency = 'eth', 'cop'
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

        #batch_response = buda.batch_creation(orders)
        #print(json.dumps(batch_response, indent=2))

        batch_cancellation_response = buda.batch_cancellation(order_to_cancel)
        print(json.dumps(batch_cancellation_response, indent=2))

        #new_order = buda.new_order(base_currency, quote_currency, side, order_type, order_amount, price=price)
        binance_ln_invoice = 'lnbc20u1pn57w8spp5tte7449lywmexq0e5zrukh97d3r797t2h38hc7znnwfpmlpywjfqdqqcqzysxqrrsssp5nmydq5cy9vjlht5nuekrk9h2y52lyd5sfwn7kj3upq2euja3h9ks9qxpqysgqsdlf0c5dnq60ffu3n2kvyg9fwv4zq738l54efex5jxf949tr28vyy4y70tfv86ua7wtaazq4yd3uuhrz3rlfwz638s09sr0lqgyp6egqn5qcrs'
        #withdrawal_request = buda.create_withdraw_request(coin=coin, address=binance_ln_invoice, amount=0.00002)
        #lightning_invoice = buda.create_deposit_address(amount_satoshis=5000, memo="test")
        #print(json.dumps(lightning_invoice, indent=2))
        #print(json.dumps(new_order, indent=2))
        #order_canceled = buda.cancel_order(base_currency, quote_currency, order_id)
        #print(json.dumps(order_canceled, indent=2))
        order_states = buda.get_order_states(base_currency, quote_currency)
        print(json.dumps(order_states, indent=2))
        #ltc_withdrawal = buda.create_withdraw_request(coin='ltc', amount=0.00702, address=ltc_address, simulate=True)
        #print(json.dumps(ltc_withdrawal, indent=2))
        #order_book = buda.get_order_book(base_currency='btc', quote_currency='usdc')
        #print(json.dumps(order_book, indent=2))
    except Exception as e:
        print(f"Error with BUDA: {e}")


if __name__ == "__main__":
    main()

