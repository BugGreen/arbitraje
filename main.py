import json
from src.exchange_api.exchange_factory import ExchangeFactory
import requests


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
        market_symbol = 'BTCUSDT'
        price = 90000
        side = 'BUY'
        time_in_force = 'GTC'
        order_type = 'LIMIT'
        #coin_info = binance.supports_lightning_network(coin)
        #withdraw_request = binance.create_withdraw_request(coin=coin, address=ln_invoice, amount=sats_amount)
        #print(json.dumps(withdraw_request, indent=2))
        #new_order = binance.new_order(symbol=market_symbol, side=side, order_type=order_type, price=price, quantity=order_amount, time_in_force=time_in_force)
        #print(json.dumps(new_order, indent=2))

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
        #binance_ln_invoice = 'lnbc20u1pn5swdvpp573v84cg3440zgzp9c3wzg0xef62ql4wxgyw2peq4lkpfclqp79gsdqqcqzysxqrrsssp58736wslm5tw8r9eep0fmysj60mf705e5dkk24nxyhpvnp5naaasq9qxpqysgqdfrr8ry3lvrpekepjj9dxualwea305v2craa5c8qy6ww9809tyeksg8s7tue5h3g48xdldc8y3hlfcvx952dk44wl60uprznqx4ehnqpaxjxfv'
        #withdrawal_request = buda.create_withdraw_request(coin=coin, address=binance_ln_invoice, amount=0.00002)
        #lightning_invoice = buda.create_deposit_address(amount_satoshis=5000, memo="test")
        #print(json.dumps(lightning_invoice, indent=2))
        #print(json.dumps(withdrawal_request, indent=2))

    except Exception as e:
        print(f"Error with BUDA: {e}")


if __name__ == "__main__":
    main()

