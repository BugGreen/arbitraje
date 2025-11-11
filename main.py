from src.exchange_api.exchange_factory import ExchangeFactory


def main() -> None:
    """
    Main function to run the arbitrage bot.
    """
    # Example usage with Binance
    try:
        binance = ExchangeFactory.get_exchange("binance")
        coin = "BTC"
        is_supported = binance.supports_lightning_network(coin)
        print(f"Binance BTC Lightning Support: {is_supported}")
    except Exception as e:
        print(f"Error with Binance: {e}")

    # Example usage with BUDA
    try:
        buda = ExchangeFactory.get_exchange("buda")
        coin = "BTC"
        is_supported = buda.supports_lightning_network(coin)
        print(f"BUDA BTC Lightning Support: {is_supported}")
    except Exception as e:
        print(f"Error with BUDA: {e}")


if __name__ == "__main__":
    main()
