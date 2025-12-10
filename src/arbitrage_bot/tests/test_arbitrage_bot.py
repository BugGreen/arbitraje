from src.arbitrage_bot.arbitrage_bot import ArbitrageBot


def test_get_price_difference():
    # Setup
    bot = ArbitrageBot(exchange_a='binance', exchange_b='buda', price_difference=1.0, mode='aggressive',
                       base_currency='btc', quote_currency='usd', amount=1000)

    # Test if the price difference is correctly calculated
    price_diff = bot.get_price_difference()
    assert isinstance(price_diff, float), "Price difference should be a float."
    assert price_diff >= 0, "Price difference should be positive or zero."


def test_execute_arbitrage():
    # ToDo
    pass
