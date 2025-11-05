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
        #coin_info = binance.supports_lightning_network(coin)
        #withdraw_request = binance.create_withdraw_request(coin=coin, address=ln_invoice, amount=sats_amount)
        #print(json.dumps(withdraw_request, indent=2))

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
        lightning_invoice = buda.create_deposit_address(amount_satoshis=5000, memo="test")
        print(json.dumps(lightning_invoice, indent=2))
    except Exception as e:
        print(f"Error with BUDA: {e}")


if __name__ == "__main__":
    main()

