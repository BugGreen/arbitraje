import json
from src.arbitrage_bot.arbitrage_bot import ArbitrageBot
from unittest.mock import patch
import unittest
from typing import List, Dict, Any
import logging


# Configure logging to display INFO level messages on the console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_get_price_difference():
    # Setup
    bot = ArbitrageBot(exchange_high_liquidity='binance', exchange_low_liquidity='buda', price_diff_threshold=1.0, mode='aggressive',
                       base_currency='btc', quote_currency='usd', amount=1000)

    # Test if the price difference is correctly calculated
    price_diff = bot.get_price_difference()
    assert isinstance(price_diff, float), "Price difference should be a float."
    assert price_diff >= 0, "Price difference should be positive or zero."


class MockExchange:
    """
    A mock exchange class to simulate the `get_order_states` response.
    """
    def __init__(self, orders: List[Dict[str, Any]]):
        self.mock_orders = orders

    def get_order_states(self, base_currency, quote_currency) -> Dict[str, Any]:
        return {"orders": self.mock_orders}


class TestArbitrageBot(unittest.TestCase):

    mock_orders = [
        {
            "id": 397656360,
            "uuid": "96fbfb86-4c98-429b-a73d-07a5d0233c68",
            "market_id": "ETH-COP",
            "account_id": 143870,
            "type": "Ask",
            "state": "traded",
            "created_at": "2023-01-06T18:08:20.429Z",
            "fee_currency": "COP",
            "price_type": "limit",
            "order_type": "gtc",
            "expire_at": 0,
            "limit": [
                "5996660.7",
                "COP"
            ],
            "amount": [
                "0.0",
                "ETH"
            ],
            "original_amount": [
                "0.033351895",
                "ETH"
            ],
            "traded_amount": [
                "0.033351895",
                "ETH"
            ],
            "total_exchanged": [
                "199999.99",
                "COP"
            ],
            "paid_fee": [
                "699.99",
                "COP"
            ],
        },
        {
            "id": 397122183,
            "uuid": "dba0dedc-25b8-40de-a6dd-a226a7a87d49",
            "market_id": "ETH-COP",
            "account_id": 143870,
            "type": "Bid",
            "state": "traded",
            "created_at": "2023-01-06T00:40:44.531Z",
            "fee_currency": "ETH",
            "price_type": "limit",
            "order_type": "gtc",
            "expire_at": 0,
            "limit": [
                "5918173.16",
                "COP"
            ],
            "amount": [
                "0.0",
                "ETH"
            ],
            "original_amount": [
                "0.004710184",
                "ETH"
            ],
            "traded_amount": [
                "0.004710184",
                "ETH"
            ],
            "total_exchanged": [
                "27875.68",
                "COP"
            ],
            "paid_fee": [
                "0.000016485",
                "ETH"
            ],
        }]

    @patch.object(ArbitrageBot, '_create_exchange', return_value=MockExchange(mock_orders))
    def test_check_sub_orders_status_all_found(self, mock_get_exchange):
        """
        Test that when all provided sub_order_ids exist in the exchange's order states,
        the method returns their respective statuses.
        """

        bot = ArbitrageBot(exchange_high_liquidity='binance',
                           exchange_low_liquidity='buda',
                           base_currency="ETH", quote_currency="COP",
                           price_diff_threshold=10.0, amount=10)

        sub_order_ids = ["397656360", "397122183"]
        result = bot.check_sub_orders_status(sub_order_ids)
        # print(json.dumps(result, indent=2))
        self.assertEqual(len(result), 2)
        self.assertEqual(result.get("397656360")["state"], "traded")
        self.assertEqual(result.get("397122183")["state"], "traded")

    @patch.object(ArbitrageBot, '_create_exchange', return_value=MockExchange(mock_orders))
    def test_split_order_into_suborders_ask_with_delta(self, mock_get_exchange):
        """
        Test splitting an 'ask' order with a specified delta.
        """
        bot = ArbitrageBot(exchange_high_liquidity=None,
                           exchange_low_liquidity=None,
                           base_currency="ETH", quote_currency="COP",
                           price_diff_threshold=10.0, amount=10)

        order_amount = 100.0
        reference_price = 10000.0
        delta = 50.0
        side = 'ask'

        result = bot.split_order_into_suborders(order_amount, reference_price, side, delta=delta)

        print(json.dumps(result, indent=2))
        # Check amount distribution
        self.assertEqual(result[0]["order"]["amount"], 60.0)
        self.assertEqual(result[1]["order"]["amount"], 30.0)
        self.assertEqual(result[2]["order"]["amount"], 10.0)

        # Check price calculations
        expected_one_price = reference_price + delta  # 10000 + 50 = 10050
        expected_two_price = expected_one_price * 1.001
        expected_three_price = expected_one_price * 1.002
        self.assertAlmostEqual(result[0]["order"]["limit"], expected_one_price)
        self.assertAlmostEqual(result[1]["order"]["limit"], expected_two_price)
        self.assertAlmostEqual(result[2]["order"]["limit"], expected_three_price)

    @patch.object(ArbitrageBot, '_create_exchange', return_value=MockExchange(mock_orders))
    def test_split_order_into_suborders_bid_no_delta(self, mock_get_exchange):
        """
        Test splitting a 'bid' order without a delta (uses price_diff_treshold).
        """
        bot = ArbitrageBot(exchange_high_liquidity=None,
                           exchange_low_liquidity=None,
                           base_currency="ETH", quote_currency="COP",
                           price_diff_threshold=10.0, amount=10)

        order_amount = 200.0
        reference_price = 5000.0
        # No delta given
        side = 'bid'

        result = bot.split_order_into_suborders(order_amount, reference_price, side)

        # Check amount distribution
        self.assertEqual(result[0]["order"]["amount"], 120.0)  # 60% of 200
        self.assertEqual(result[1]["order"]["amount"], 60.0)  # 30% of 200
        self.assertEqual(result[2]["order"]["amount"], 20.0)  # 10% of 200

        # Check price calculations: reference_price - price_diff_treshold (5000 - 10 = 4990)
        expected_one_price = 4990
        expected_two_price = 4990 * 0.999
        expected_three_price = 4990 * 0.998
        self.assertAlmostEqual(result[0]["order"]["limit"], expected_one_price)
        self.assertAlmostEqual(result[1]["order"]["limit"], expected_two_price)
        self.assertAlmostEqual(result[2]["order"]["limit"], expected_three_price)
