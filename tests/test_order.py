from src.arbitrage_bot.order import Order


def test_order_initialization():
    order = Order('BTC', 'USD', 1000, order_type='BUDA_bid_limit')
    assert order.base_currency == 'BTC'
    assert order.quote_currency == 'USD'
    assert order.amount == 1000
    assert order.order_type == 'BUDA_bid_limit'
    assert order.variable_costs == 0.001  # 0.1% as variable cost
    assert order.fixed_costs == 6  # 6 USDC as fixed cost


def test_order_fulfillment():
    order = Order('BTC', 'USD', 1000, order_type='BUDA Bid Limit')
    order.add_trade({'amount': 300, 'price': 30000})
    order.add_trade({'amount': 700, 'price': 31000})
    assert order.is_fulfilled() is True
    assert order.get_remaining_amount() == 0


def test_add_trade():
    order = Order(base_currency="btc", quote_currency="usd", amount=1000)
    order.add_trade({'exchange': 'Buda', 'amount': 300})
    assert len(order.trades) == 1
    assert order.trades[0]['amount'] == 300

