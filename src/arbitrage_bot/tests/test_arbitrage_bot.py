import json
from src.arbitrage_bot.arbitrage_bot import ArbitrageBot
from src.exchange_api.buda_proxy import BudaProxy
from unittest.mock import patch, MagicMock
import unittest
from typing import List, Dict, Any
import logging
from src.exchange_api.tests import constants as test_api_constants
from src.arbitrage_bot.tests import constants as test_a_bot_constans


logger = logging.getLogger(__name__)


def test_get_price_difference():
    # Setup
    bot = ArbitrageBot(exchange_high_liquidity='binance', exchange_low_liquidity='buda', price_diff_threshold=1.0,
                       mode='aggressive', base_currency='btc', quote_currency='usd', amount=1000)

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


class MockBudaProxySuccess():
    """
    Mock proxy for successful batch creation.
    """
    @staticmethod
    def batch_creation(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        return [
            {
                "id": "1306565374",
                "status": "received",
                "error_message": None
            },
            {
                "id": "1306565375",
                "status": "received",
                "error_message": None
            }
        ]


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
    def setUp(self, mock_get_exchange):
        # Initialize ArbitrageBot with BudaProxy
        self.bot = ArbitrageBot(
            exchange_high_liquidity='binance',
            exchange_low_liquidity='buda',
            price_diff_threshold=10.0,
            mode='conservative',
            base_currency='ETH',
            quote_currency='COP',
            amount=0.05  # Example amount
        )
        self.bot.exchange_low_liquidity = BudaProxy()

    def test_check_sub_orders_status_all_found(self):
        """
        Test that when all provided sub_order_ids exist in the exchange's order states,
        the method returns their respective statuses.
        """

        sub_order_ids = ["397656360", "397122183"]
        result = self.bot.check_sub_orders_status(sub_order_ids)
        # print(json.dumps(result, indent=2))
        self.assertEqual(len(result), 2)
        self.assertEqual(result.get("397656360")["state"], "traded")
        self.assertEqual(result.get("397122183")["state"], "traded")

    def test_split_order_into_suborders_ask_with_delta(self):
        """
        Test splitting an 'ask' order with a specified delta.
        """

        order_amount = 100.0
        reference_price = 10000.0
        delta = 50.0
        side = 'ask'

        result = self.bot.split_order_into_suborders(order_amount, reference_price, side, delta=delta)

        # print(json.dumps(result, indent=2))
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

    def test_split_order_into_suborders_bid_no_delta(self):
        """
        Test splitting a 'bid' order without a delta (uses price_diff_treshold).
        """

        order_amount = 200.0
        reference_price = 5000.0
        # No delta given
        side = 'bid'

        result = self.bot.split_order_into_suborders(order_amount, reference_price, side)

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

    def test_split_order_with_min_amounts_merge_required(self):
        """
        If a sub-order is below the minimum amount, it should be merged into the next (or previous).
        For ETH-COP (min=0.001). Create sub-orders that are partly below that threshold.
        """
        # Splitting:

        #   sub_order_one_amount: 0.0012 * 0.6 = 0.00072
        #   sub_order_two_amount: 0.0012 * 0.3 = 0.00036
        #   sub_order_three_amount: 0.0012 * 0.1 = 0.00012

        # All of these are below 0.001, so each will attempt to merge with the next.

        sub_orders = self.bot.split_order_into_suborders(
            order_amount=0.0012,
            reference_price=10000.0,
            side='bid',
            delta=50.0
        )

        # Because sub_order_one_amount < min, it merges into sub_order two.
        # Then sub_order two merges into sub_order three, or vice versa.
        # The final result might be:
        #   [ {...}, {...} ] or [ {...} ] (depending on merging logic)

        self.assertGreaterEqual(len(sub_orders), 1, "We should end up with at least one sub-order.")

        # Check that each final sub-order is >= the min amount (0.001)
        for so in sub_orders:
            self.assertGreaterEqual(so["order"]["amount"], 0.001, "Merged sub-orders must meet the minimum amount.")

    def test_below_min_total_returns_error(self):
        result = self.bot.split_order_into_suborders(
            order_amount=0.000009,
            reference_price=15000,
            side='ask'
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('code'), 'ERROR_BELOW_MIN_TOTAL')

    @patch.object(BudaProxy, 'get_order_states', return_value=test_api_constants.successful_batch_order_states)
    @patch('requests.post')
    def test_place_sub_orders_success(self, mock_post, mock_buda):
        # Remember that bot.exchange_low_liquidity was defined in the `set` method

        mock_response = MagicMock()
        mock_response.json.return_value = test_api_constants.successful_batch_order_mock_response

        mock_post.return_value = mock_response

        sub_orders_example = test_api_constants.successful_batch_order

        # Mock the requests.post in batch_creation method of exchange_low_liquidity object
        response = self.bot.place_sub_orders(sub_orders_example)
        expected_response = test_api_constants.expected_successful_batch_order_response
        for order in expected_response:
            order['status'] = 'pending'

        self.assertEqual(response, expected_response)

    @patch('requests.post')
    def test_place_sub_orders_partial_success(self, mock_post) -> None:
        """
        Test when batch order is tried to be created, but a sub_order is intended to be created with more than
        the available amount (causing an 'insolvent' error in BUDA)

        :param mock_post: mock object
        :return: None
        """
        # Remember that bot.exchange_low_liquidity was defined in the `set` method

        mock_response = MagicMock()
        mock_response.json.return_value = test_api_constants.partial_successful_batch_order_mock_response

        mock_post.return_value = mock_response

        partial_correct_sub_orders = test_api_constants.partial_successful_batch_order

        place_sub_orders_response = self.bot.place_sub_orders(partial_correct_sub_orders)
        expected_response = test_a_bot_constans.expected_insolvent_error_response

        self.assertEqual(place_sub_orders_response, expected_response)

    @patch('requests.post')
    def test_place_sub_orders_amount_less_than_minimum(self, mock_post) -> None:
        """
        Test when batch order is tried to be created, but a sub_order is intended to be created with less than
        the allowed minimum amount (causing an 'EXCHANGE_API_ERROR_invalid_record' error in BUDA)

        :param mock_post: mock object
        :return: None
        """

        mock_response = MagicMock()
        mock_response.json.return_value = test_api_constants.amount_less_than_minimum_order_mock_response

        mock_post.return_value = mock_response

        amount_less_than_minimum_order = test_api_constants.amount_less_than_minimum_order

        amount_less_than_minimum_order_response = self.bot.place_sub_orders(amount_less_than_minimum_order)
        expected_response = test_a_bot_constans.expected_amount_less_than_minimum_response  # Wrapped response in A.Bot

        self.assertEqual(amount_less_than_minimum_order_response, expected_response)

