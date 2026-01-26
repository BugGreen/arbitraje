from src.arbitrage_bot.arbitrage_bot import ArbitrageBot
from src.order_types.arbitrage_order import ArbitrageOrder
from exchange_api.low_liquidity_exchanges.buda_proxy import BudaProxy
from exchange_api.high_liquidity_exchanges.binance_proxy import BinanceProxy
from unittest.mock import patch, MagicMock
import unittest
from typing import List, Dict, Any, Union, Optional
import logging
from tests import exchange_constants as test_api_constants, a_bot_constants as test_a_bot_constans
from src.order_types.encoders import OrderType, CurrencyOfInterest


logger = logging.getLogger(__name__)


class MockExchange:
    """
    A mock exchange class to simulate the `get_order_states` response.
    """
    def __init__(self, orders: List[Dict[str, Any]]):
        self.mock_orders = orders

    def get_order_states(self, base_currency, quote_currency) -> Dict[str, Any]:
        return {"orders": self.mock_orders}


class MockArbitrageOrder:
    """
    Simple mock substituting ArbitrageOrder for testing.
    """
    def __init__(self, original_amount: float):
        self.original_amount = original_amount
        self.pending_amount_low_liquidity = original_amount
        self.order_type = OrderType.BUY_LIMIT


class MockBudaProxySuccess():
    """
    Mock proxy for successful batch creation.
    """
    @staticmethod
    def batch_creation(self, orders: List[Dict[str, Any]]) -> List[
        Union[Dict[str, Optional[str]], Dict[str, Optional[str]]]]:
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
            price_diff_threshold=0.4,
            mode='conservative',
            base_currency='ETH',
            quote_currency='COP',
        )
        self.bot.exchange_low_liquidity = BudaProxy()
        self.bot.exchange_high_liquidity = BinanceProxy()
        self.arb_order = ArbitrageOrder(
            base_currency="ETH",
            quote_currency="COP",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )

    def test_split_order_into_suborders_ask_with_delta(self):
        """
        Test splitting an 'ask' order with a specified delta.
        """

        mock_order = MockArbitrageOrder(original_amount=100.0)
        reference_price = 10000.0
        delta = 0.5 / 100
        mock_order.order_type = OrderType.SELL_LIMIT
        mock_order.base_currency, mock_order.quote_currency = "BTC", "USDC"

        result = self.bot.split_order_into_suborders(mock_order, reference_price, delta=delta)

        # print(json.dumps(result, indent=2))
        # Check amount distribution
        self.assertEqual(result[0]["order"]["amount"], 60.0 / result[0]["order"]["limit"])
        self.assertEqual(result[1]["order"]["amount"], 30.0 / result[1]["order"]["limit"])
        self.assertEqual(result[2]["order"]["amount"], 10.0 / result[2]["order"]["limit"])

        # Check price calculations
        expected_one_price = reference_price * (1 + delta + self.bot.price_diff_threshold)  # 10000 + 50 = 10050
        expected_two_price = expected_one_price * 1.001
        expected_three_price = expected_one_price * 1.002
        self.assertAlmostEqual(result[0]["order"]["limit"], expected_one_price)
        self.assertAlmostEqual(result[1]["order"]["limit"], expected_two_price)
        self.assertAlmostEqual(result[2]["order"]["limit"], expected_three_price)

    def test_split_order_into_suborders_bid_no_delta(self):
        """
        Test splitting a 'bid' order without a delta (uses price_diff_treshold).
        """

        mock_order = MockArbitrageOrder(original_amount=200.0)
        mock_order.base_currency, mock_order.quote_currency = "BTC", "USDC"

        reference_price = 5000.0
        # No delta given

        result = self.bot.split_order_into_suborders(mock_order, reference_price)

        # Check amount distribution
        self.assertEqual(result[0]["order"]["amount"], 120.0 / result[0]["order"]["limit"])  # 60% of 200 in Base Currency
        self.assertEqual(result[1]["order"]["amount"], 60.0 / result[1]["order"]["limit"])  # 30% of 200
        self.assertEqual(result[2]["order"]["amount"], 20.0 / result[2]["order"]["limit"])  # 10% of 200

        # Check price calculations: reference_price - price_diff_treshold (5000 - 10 = 4990)
        expected_one_price = reference_price * (1 - self.bot.price_diff_threshold)
        expected_two_price = expected_one_price * 0.999
        expected_three_price = expected_one_price * 0.998
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

        mock_order = MockArbitrageOrder(original_amount=15)
        mock_order.base_currency, mock_order.quote_currency = "BTC", "USDC"

        sub_orders = self.bot.split_order_into_suborders(
            arb_order=mock_order,
            reference_price=10000.0,
            delta=.5 / 100
        )

        # Because sub_order_one_amount < min, it merges into sub_order two.
        # Then sub_order two merges into sub_order three, or vice versa.
        # The final result might be:
        #   [ {...}, {...} ] or [ {...} ] (depending on merging logic)

        self.assertGreaterEqual(len(sub_orders), 1, "We should end up with at least one sub-order.")

        # Check that each final sub-order is >= the min amount (0.001)
        for so in sub_orders:
            self.assertGreaterEqual(so["order"]["amount"], 0.00002, "Merged sub-orders must meet the minimum amount.")

    def test_below_min_total_returns_error(self):

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=0.000009,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        result = self.bot.split_order_into_suborders(
            arb_order=arb_order,
            reference_price=15000,
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('code'), 'ERROR_BELOW_MIN_TOTAL')

    @patch.object(BudaProxy, 'get_order_states', return_value=test_api_constants.successful_batch_order_states_pending)
    @patch('requests.post')
    def test_place_sub_orders_success(self, mock_post, mock_buda):
        # Remember that bot.exchange_low_liquidity was defined in the `set` method

        mock_response = MagicMock()
        mock_response.json.return_value = test_api_constants.successful_batch_order_mock_response

        mock_post.return_value = mock_response

        sub_orders_example = test_api_constants.successful_batch_order

        # Mock the requests.post in batch_creation method of exchange_low_liquidity object
        response = self.bot.place_sub_orders(sub_orders_example, self.arb_order)
        expected_response = test_api_constants.expected_successful_batch_order_response
        for order in expected_response:
            order['status'] = 'pending'

        self.assertEqual(response, expected_response)

    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.successful_batch_order_states_sub_orders_traded)
    @patch('requests.post')
    @patch.object(ArbitrageBot, 'execute_opposite_order_high_liquidity_exchange', return_value=None)
    def test_place_sub_orders_traded(self, mock_opposite_order, mock_post, mock_buda):
        # Change the state of the first sub_order to "traded"
        test_api_constants.successful_batch_order_states_sub_orders_traded["orders"][0]["state"] = "traded"
        # Change the traded_amount '0.0' > '0.4'.
        test_api_constants.successful_batch_order_states_sub_orders_traded["orders"][0]["traded_amount"][0] = "0.4"
        mock_response = MagicMock()
        mock_response.json.return_value = test_api_constants.successful_batch_order_mock_response

        mock_post.return_value = mock_response

        sub_orders_example = test_api_constants.successful_batch_order

        # Mock the requests.post in batch_creation method of exchange_low_liquidity object
        response = self.bot.place_sub_orders(sub_orders_example, self.arb_order)
        expected_response = test_api_constants.expected_successful_batch_order_response
        count = 0
        for order in expected_response:
            if count == 0:
                order['status'] = 'traded'
            else:
                order['status'] = 'pending'
            count += 1

        self.assertEqual(response, expected_response)
        self.assertIsInstance(response, list)
        # check the updated arb_order
        # As the mock trade was '0.4' ETH, some attributes should be updated accordingly
        self.assertAlmostEqual(self.arb_order.traded_quote_amount_low_liquidity, 12000, places=4)
        self.assertAlmostEqual(self.arb_order.pending_amount_low_liquidity, 12000, places=4)
        self.assertAlmostEqual(self.arb_order._pending_quote_amount_high_liquidity, 12000, places=4)
        self.assertAlmostEqual(self.arb_order._pending_base_amount_high_liquidity, 0.4, places=4)

    @patch.object(BudaProxy, 'get_order_states', return_value=test_api_constants.successful_batch_order_states)
    @patch('requests.post')
    @patch.object(ArbitrageBot, 'execute_opposite_order_high_liquidity_exchange', return_value=None)
    def test_place_sub_orders_canceled_and_traded(self, mock_opposite_order, mock_post, mock_buda):
        # Change the state of the first sub_order to "traded"
        test_api_constants.successful_batch_order_states["orders"][0]["state"] = "canceled_and_traded"
        # Change the traded_amount '0.0' > '0.4'.
        test_api_constants.successful_batch_order_states["orders"][0]["traded_amount"][0] = "0.6"
        test_api_constants.successful_batch_order_states["orders"][0]["total_exchanged"][0] = "6000000.0"
        test_api_constants.successful_batch_order_states["orders"][1]["state"] = "traded"
        # Change the traded_amount '0.0' > '0.6'.
        test_api_constants.successful_batch_order_states["orders"][1]["traded_amount"][0] = "0.4"
        test_api_constants.successful_batch_order_states["orders"][1]["total_exchanged"][0] = "4000000.0"

        mock_response = MagicMock()
        mock_response.json.return_value = test_api_constants.successful_batch_order_mock_response

        mock_post.return_value = mock_response

        sub_orders_example = test_api_constants.successful_batch_order

        # Mock the requests.post in batch_creation method of exchange_low_liquidity object
        self.arb_order.pending_amount_low_liquidity = 10000000.0
        response = self.bot.place_sub_orders(sub_orders_example, self.arb_order)
        expected_response = test_api_constants.expected_successful_batch_order_response
        count = 0
        for order in expected_response:
            if count == 0:
                order['status'] = 'canceled_and_traded'
            else:
                order['status'] = 'traded'
            count += 1

        self.assertEqual(response, expected_response)
        self.assertIsInstance(response, list)
        # check the updated arb_order
        # As the mock trade was '0.4' ETH, some attributes should be updated accordingly
        self.assertAlmostEqual(self.arb_order.traded_quote_amount_low_liquidity, 10000000, places=4)
        self.assertAlmostEqual(self.arb_order.pending_amount_low_liquidity, 0.0, places=4)
        self.assertAlmostEqual(self.arb_order._pending_quote_amount_high_liquidity, 10000000, places=4)
        self.assertAlmostEqual(self.arb_order._pending_base_amount_high_liquidity, 1.0, places=4)

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

        place_sub_orders_response = self.bot.place_sub_orders(partial_correct_sub_orders, self.arb_order)
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

        amount_less_than_minimum_order_response = self.bot.place_sub_orders(amount_less_than_minimum_order,
                                                                            self.arb_order)
        expected_response = test_a_bot_constans.expected_amount_less_than_minimum_response  # Wrapped response in A.Bot

        self.assertEqual(amount_less_than_minimum_order_response, expected_response)

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_after_cancelaion_profit)
    @patch.object(BudaProxy, 'batch_cancellation', return_value=test_api_constants.sub_orders_canceled_response)
    @patch.object(BudaProxy, 'get_order_states', return_value=test_api_constants.sub_orders_to_cancel_states)
    @patch.object(ArbitrageBot, 'place_sub_orders',
                  return_value=test_a_bot_constans.placed_sub_orders_to_cancel_response)
    def test_cancel_sub_orders(self, place_sub_orders_mock, get_order_states_mock, batch_cancellation_mock,
                               new_order_mock):
        """
        Test place_sub_order_cancelations with sub_orders from place_sub_orders
        """
        # 1. Suppose we place sub-orders
        sub_orders = [
            {"mode": "place", "order": {"amount": 0.3, "limit": 10000.0}},
            {"mode": "place", "order": {"amount": 0.7, "limit": 10000.0}}
        ]

        place_response = self.bot.place_sub_orders(sub_orders, self.arb_order)

        arb_order = ArbitrageOrder(
            base_currency="ETH",
            quote_currency="USDC",
            original_amount=10000,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        # We expect place_response to have sub-orders with IDs: 130000, 130001
        # and status 'received'
        self.assertEqual(len(place_response), 2)
        self.assertEqual(place_response[0]["id"], 130000)
        self.assertEqual(place_response[0]["status"], "received")

        # 2. Now we want to cancel them
        cancel_response = self.bot.place_sub_order_cancellations(place_response, arb_order)

        # We expect a list of cancel requests with mode='cancel' and order_id=...
        self.assertEqual(len(cancel_response), 2)
        self.assertEqual(cancel_response, test_a_bot_constans.expected_sub_orders_cancelled_response)
        self.assertEqual(arb_order.profit.amount, 299.9888596 )
        self.assertEqual(arb_order.profit.currency, 'USDC')
        self.assertEqual(arb_order.traded_amount_quote_high_liquidity, 3300)
        self.assertEqual(arb_order.traded_quote_amount_low_liquidity, 3000)
        self.assertEqual(arb_order.pending_amount_low_liquidity, 7000)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, arb_order.traded_amount_base_high_liquidity)

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response)
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation', return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance_buy_limit)
    def test_synchronous_opposite_order_buy_limit_quote_profit(self, batch_creation_mock, get_order_states_mock,
                                                               binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` with profit
        i.e., high_liquidity_exchange_price > low_liquidity_exchange_price.
        In this case, the currency of interest is the quote one.
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},  # Just an example
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        low_liquidity_price = 1000
        high_liquidity_price = 1100
        price_diff_buy_limit = (high_liquidity_price - low_liquidity_price) / low_liquidity_price
        paid_fees_quote_currency = 0.01114035
        traded_ratio = 1
        traded_quote_amount = 200 * traded_ratio

        expected_profit_quote_amount = round((traded_quote_amount * price_diff_buy_limit) - paid_fees_quote_currency, 7)
        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertAlmostEqual(arb_order._pending_quote_amount_high_liquidity, 0.0)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, arb_order.traded_amount_base_high_liquidity)
        self.assertAlmostEqual(arb_order.traded_amount_quote_high_liquidity, 220.0)
        self.assertEqual(arb_order.profit.amount, expected_profit_quote_amount)
        self.assertEqual(arb_order.profit.currency, 'USDC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_base)
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation', return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance.copy())
    def test_synchronous_opposite_order_buy_limit_base_profit(self, batch_creation_mock, get_order_states_mock,
                                                              binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` with actual profit
        i.e., high_liquidity_exchange_price > low_liquidity_exchange_price.
        In this case, the currency of interest is the base one.
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'
        self.bot.currency_of_interest = CurrencyOfInterest.BASE

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            amount=1000.0,
            currency_of_interest=CurrencyOfInterest.BASE,
            order_type=OrderType.BUY_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertAlmostEqual(arb_order._pending_base_amount_high_liquidity, 0.0, places=4)
        self.assertAlmostEqual(round(arb_order.traded_amount_quote_high_liquidity, 1), 200.0, places=4)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, 1.0)
        self.assertEqual(arb_order.traded_amount_base_high_liquidity + arb_order.profit.amount,
                         arb_order.traded_base_amount_low_liquidity)
        self.assertAlmostEqual(arb_order.profit.amount, 0.01819, places=4)
        self.assertEqual(arb_order.profit.currency, 'BTC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_base_no_profit)
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation', return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance.copy())
    def test_synchronous_opposite_order_buy_limit_base_no_profit(self, batch_creation_mock, get_order_states_mock,
                                                                 binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` without profit
        i.e., high_liquidity_exchange_price < low_liquidity_exchange_price.
        In this case, the currency of interest is the base one.
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'
        self.bot.currency_of_interest = CurrencyOfInterest.BASE

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            amount=1000.0,
            currency_of_interest=CurrencyOfInterest.BASE,
            order_type=OrderType.BUY_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertAlmostEqual(arb_order._pending_quote_amount_high_liquidity, 0.0, places=4)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, 1.0)
        self.assertEqual(arb_order.traded_amount_base_high_liquidity + arb_order.profit.amount,
                         arb_order.traded_base_amount_low_liquidity)
        self.assertAlmostEqual(round(arb_order.traded_amount_quote_high_liquidity, 1), 200.0, places=4)
        self.assertAlmostEqual(arb_order.profit.amount, -0.02222, places=4)
        self.assertEqual(arb_order.profit.currency, 'BTC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_quote_no_profit)
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation', return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance_quote_no_profit)
    def test_synchronous_opposite_order_buy_limit_quote_no_profit(self, batch_creation_mock, get_order_states_mock,
                                                                  binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` without profit
        i.e., high_liquidity_exchange_price < low_liquidity_exchange_price.
        In this case, the currency of interest is the base one.
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'
        self.bot.currency_of_interest = CurrencyOfInterest.QUOTE

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertAlmostEqual(arb_order._pending_base_amount_high_liquidity, 0.0, places=4)
        self.assertAlmostEqual(round(arb_order.traded_amount_quote_high_liquidity, 1), 180.0, places=4)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, arb_order.traded_amount_base_high_liquidity)
        self.assertAlmostEqual(arb_order.profit.amount, -20.0111404, places=4)
        self.assertEqual(arb_order.profit.currency, 'USDC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_quotes_profit)
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_multiple_traded_states)
    @patch.object(BudaProxy, 'batch_creation', return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance_quote_multiple_profit)
    def test_synchronous_opposite_order_buy_limit_quote_multiple_profit(self, batch_creation_mock, get_order_states_mock,
                                                                        binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` without profit
        i.e., high_liquidity_exchange_price < low_liquidity_exchange_price.
        In this case, the currency of interest is the base one.
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'
        self.bot.currency_of_interest = CurrencyOfInterest.QUOTE

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 500.0}},
            {"mode": "place", "order": {"amount": 500.0}},
        ]

        low_liquidity_price = 1000
        high_liquidity_price = 1100
        price_diff_buy_limit = (high_liquidity_price - low_liquidity_price) / low_liquidity_price
        paid_fees_quote_currency = 0.01114035 + 0.01114035
        traded_ratio = 1
        traded_quote_amount = 1000 * traded_ratio

        expected_profit_quote_amount = round((traded_quote_amount * price_diff_buy_limit) - paid_fees_quote_currency, 7)

        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 1000.0)
        self.assertAlmostEqual(arb_order._pending_base_amount_high_liquidity, 0.0, places=4)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, arb_order.traded_amount_base_high_liquidity)
        self.assertAlmostEqual(round(arb_order.traded_amount_quote_high_liquidity, 1), 1100.0, places=4)
        self.assertAlmostEqual(arb_order.profit.amount, expected_profit_quote_amount, places=4)
        self.assertEqual(arb_order.profit.currency, 'USDC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_quote_no_profit)
    @patch.object(BudaProxy, 'get_order_states', return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation', return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance.copy())
    def test_synchronous_opposite_order_sell_limit_quote_profit(self, batch_creation_mock, get_order_states_mock,
                                                                binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` with profit
        i.e., high_liquidity_exchange_price > low_liquidity_exchange_price.
        In this case, the currency of interest is the quote one.
        """
        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            amount=1000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},  # Just an example
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertAlmostEqual(arb_order._pending_quote_amount_high_liquidity, 0.0)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, arb_order.traded_amount_base_high_liquidity)
        self.assertAlmostEqual(arb_order.traded_amount_quote_high_liquidity, 180.0)
        self.assertEqual(arb_order.profit.amount, 20)
        self.assertEqual(arb_order.profit.currency, 'USDC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response)
    @patch.object(BudaProxy, 'get_order_states', return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation', return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance_quote_profit)
    def test_synchronous_opposite_order_sell_limit_quote_profit(self, batch_creation_mock, get_order_states_mock,
                                                                binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` with profit
        i.e., high_liquidity_exchange_price > low_liquidity_exchange_price.
        In this case, the currency of interest is the quote one.
        """
        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},  # Just an example
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertAlmostEqual(arb_order._pending_base_amount_high_liquidity, 0.0)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, arb_order.traded_amount_base_high_liquidity)
        self.assertAlmostEqual(arb_order.traded_amount_quote_high_liquidity, 220.0)
        self.assertEqual(arb_order.profit.amount, -20.0111404)
        self.assertEqual(arb_order.profit.currency, 'USDC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_base_no_profit)
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation',
                  return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance_base_profit)
    def test_synchronous_opposite_order_buy_limit_base_profit(self, batch_creation_mock, get_order_states_mock,
                                                              binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` with actual profit
        i.e., high_liquidity_exchange_price > low_liquidity_exchange_price.
        In this case, the currency of interest is the base one.
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'
        self.bot.currency_of_interest = CurrencyOfInterest.BASE

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            currency_of_interest=CurrencyOfInterest.BASE,
            order_type=OrderType.SELL_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertAlmostEqual(arb_order._pending_base_amount_high_liquidity, 0, places=4)
        self.assertAlmostEqual(arb_order.get_pending_quote_amount_high_liquidity, 0.0020000000000095497, places=4)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, 0.2)
        self.assertAlmostEqual(round(arb_order.traded_amount_quote_high_liquidity, 1), 200.0, places=4)
        self.assertAlmostEqual(arb_order.profit.amount, 0.0222199, places=4)
        self.assertEqual(arb_order.profit.currency, 'BTC')

    @patch.object(BinanceProxy, 'new_order',
                  return_value=test_api_constants.binance_successful_sell_market_order_response_base)
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_states)
    @patch.object(BudaProxy, 'batch_creation',
                  return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance.copy())
    def test_synchronous_opposite_order_buy_limit_base_no_profit(self, batch_creation_mock, get_order_states_mock,
                                                                 binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` with actual profit
        i.e., high_liquidity_exchange_price > low_liquidity_exchange_price.
        In this case, the currency of interest is the base one.
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'
        self.bot.currency_of_interest = CurrencyOfInterest.BASE

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            currency_of_interest=CurrencyOfInterest.BASE,
            order_type=OrderType.SELL_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        low_liquidity_price = 1000
        high_liquidity_price = 1100
        price_diff_sell_limit = (low_liquidity_price - high_liquidity_price) / high_liquidity_price
        paid_fees_base_currency = 1.012759090909091e-05
        traded_ratio = 0.999955
        traded_base_amount = 0.2 * traded_ratio

        expected_profit = round((traded_base_amount * price_diff_sell_limit) - paid_fees_base_currency, 7)
        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 200.0)
        self.assertEqual(arb_order.traded_base_amount_low_liquidity, 0.2)
        self.assertAlmostEqual(arb_order._pending_base_amount_high_liquidity, 0, places=4)
        self.assertAlmostEqual(arb_order._pending_quote_amount_high_liquidity, 0.00899999999998613, places=4)
        self.assertAlmostEqual(round(arb_order.traded_amount_quote_high_liquidity, 1), 200.0, places=4)
        self.assertAlmostEqual(arb_order.traded_base_amount_low_liquidity * traded_ratio + arb_order.profit.amount,
                               arb_order.traded_amount_base_high_liquidity - 1.012759090909091e-05)
        self.assertAlmostEqual(arb_order.profit.amount, expected_profit, places=4)
        self.assertEqual(arb_order.profit.currency, 'BTC')

    @patch.object(BinanceProxy, 'new_order',
                  side_effect=[
                      test_api_constants.binance_successful_sell_market_order_response_with_less_than_minimum_1,
                      test_api_constants.binance_successful_sell_market_order_response_with_less_than_minimum_2])
    @patch.object(BudaProxy, 'get_order_states',
                  return_value=test_api_constants.sub_orders_to_execute_in_binance_states_with_one_less_than_minimum)
    @patch.object(BudaProxy, 'batch_creation',
                  return_value=test_a_bot_constans.placed_sub_orders_to_execute_in_binance_with_one_less_than_minimum)
    def test_synchronous_opposite_order_buy_limit_quote_profit_with_less_than_minimum(self,
                                                                                      batch_creation_mock,
                                                                                      get_order_states_mock,
                                                                                      binance_market_order_mock):
        """
        Simulate a successful market order (type: BUY_LIMIT) within `high_liquidity_exchange` with profit
        i.e., high_liquidity_exchange_price > low_liquidity_exchange_price.
        In this case, the currency of interest is the quote one.
        In this test, one of the sub_orders in the low_liquidity exchange are traded with an amount that is less than
        the minimum_amount allowed in the high_liquidity exchange
        """

        self.bot.base_currency = "BTC"
        self.bot.quote_currency = 'USDC'

        # 2. ArbitrageOrder: Simulation of a Buy limit order, with interest in accumulating Quote currecy
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )

        # 3. Place sub-orders on low-liquidity
        sub_orders = [
            {"mode": "place", "order": {"amount": 200.0}},  # Just an example
            {"mode": "place", "order": {"amount": 800.0}},
        ]
        self.bot.place_sub_orders(sub_orders, arb_order)

        # 4. Now, the _wait_for_orders_to_leave_received sees ID=100 => 'traded_amount': 200 => updates arb_order
        #    => calls execute_opposite_order_high_liquidity_exchange => we do a MARKET SELL of 200 => fulfill -> 200
        self.assertAlmostEqual(arb_order.traded_quote_amount_low_liquidity, 1000.0)
        self.assertAlmostEqual(arb_order._pending_base_amount_high_liquidity, 0.0)
        self.assertAlmostEqual(arb_order.traded_amount_quote_high_liquidity, 1100.0)
        self.assertEqual(round(arb_order.profit.amount, 1), 100.0)
        self.assertEqual(arb_order.profit.currency, 'USDC')

    @patch.object(BinanceProxy, 'create_lightning_invoice',
                  return_value=test_api_constants.binance_standardized_ln_invoice_00995)
    @patch.object(BudaProxy, 'create_withdraw_request',
                  return_value=test_api_constants.buda_withdrawal_response)
    @patch.object(BudaProxy, 'get_withdraw_history',
                  return_value=test_api_constants.buda_withdrawal_history)
    def test_btc_transfer_buy(self,
                              binance_invoice_creation_mock,
                              buda_withdrawal_response_mock,
                              buda_withdrawal_history_mock):
        """
        Suppose we have a BUY_LIMIT scenario with 0.017 BTC traded on the low-liquidity side.
        We expect it to be split into 2 chunks: 0.009999, 0.007001.
        """

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="COP",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        arb_order.traded_base_amount_low_liquidity = 0.000095

        transfer_completion = self.bot.btc_transfer(arb_order)
        # Check that LN invoice was created once
        binance_invoice_creation_mock.assert_called_once()
        # Check that pay_ln_invoice was called once with correct parameters
        buda_withdrawal_response_mock.assert_called_once()
        assert transfer_completion

    @patch.object(BudaProxy, 'create_lightning_invoice',
                  return_value=test_api_constants.buda_ln_invoice_001)
    @patch.object(BinanceProxy, 'create_withdraw_request',
                  return_value=test_api_constants.binance_withdrawal_response)
    @patch.object(BinanceProxy, 'get_withdraw_history',
                  return_value=test_api_constants.binance_withdrawal_history)
    def test_btc_transfer_sell(self,
                              buda_invoice_creation_mock,
                              binance_withdrawal_response_mock,
                              binance_withdrawal_history_mock):
        """
        Another scenario: SELL_LIMIT with 0.005 BTC, fits in single chunk, no splitting.
        """

        arb_order = ArbitrageOrder(
            base_currency="ETH",
            quote_currency="COP",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        arb_order.traded_base_amount_low_liquidity = 0.000095

        transfer_completion = self.bot.btc_transfer(arb_order)
        # Check that LN invoice was created once
        buda_invoice_creation_mock.assert_called_once()
        # Check that pay_ln_invoice was called once with correct parameters
        binance_withdrawal_response_mock.assert_called_once()
        assert transfer_completion

    @patch.object(BinanceProxy, 'create_withdraw_request',
                  return_value=test_api_constants.binance_withdrawal_usdc_response)
    @patch.object(BinanceProxy, 'get_withdraw_history',
                  return_value=test_api_constants.binance_withdrawal_history_USDC)
    def test_quote_transfer_buy(self, binance_withdrawal_response_mock, binance_withdrawal_history_mock):
        """
        Suppose we have a BUY_LIMIT scenario with 0.017 BTC traded on the low-liquidity side.
        We expect it to be split into 2 chunks: 0.009999, 0.007001.
        """

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        arb_order.traded_base_amount_low_liquidity = 0.000095
        arb_order.traded_quote_amount_low_liquidity = 21

        transfer_completion = self.bot.quote_currency_transfer(arb_order)
        # Check that LN invoice was created once
        binance_withdrawal_history_mock.assert_called_once()
        assert transfer_completion

    @patch.object(BudaProxy, 'create_withdraw_request',
                   return_value=test_api_constants.buda_withdrawal_usdc_response)
    @patch.object(BudaProxy, 'get_withdraw_history',
                  return_value=test_api_constants.buda_usdc_withdrawal_history)
    def test_quote_transfer_sell(self, buda_withdrawal_response_mock, buda_withdrawal_history_usdc):
        """
        Suppose we have a SELL_LIMIT scenario with 0.017 BTC traded on the low-liquidity side.
        We expect it to be split into 2 chunks: 0.009999, 0.007001.
        """

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        arb_order.traded_base_amount_low_liquidity = 0.000095
        arb_order.traded_quote_amount_low_liquidity = 20

        transfer_completion = self.bot.quote_currency_transfer(arb_order)
        # Check that LN invoice was created once
        # binance_withdrawal_history_mock.assert_called_once()
        assert transfer_completion

    @patch.object(BinanceProxy, 'create_lightning_invoice',
                  return_value=test_api_constants.binance_standardized_ln_invoice_00995)
    @patch.object(BudaProxy, 'create_withdraw_request',
                  return_value=test_api_constants.buda_withdrawal_response)
    @patch.object(BudaProxy, 'get_withdraw_history',
                  return_value=test_api_constants.buda_withdrawal_history)
    @patch.object(BinanceProxy, 'create_withdraw_request',
                  return_value=test_api_constants.binance_withdrawal_usdc_response)
    @patch.object(BinanceProxy, 'get_withdraw_history',
                  return_value=test_api_constants.binance_withdrawal_history_USDC)
    def test_funds_transfer_buy_order(self,
                            binance_invoice_creation_mock,
                            buda_withdrawal_response_mock,
                            buda_withdrawal_history_mock,
                            binance_withdrawal_response_mock,
                            binance_withdrawal_history_mock):
        """
        Suppose we have a BUY_LIMIT scenario with 0.000095 BTC traded on the low-liquidity side.
        We expect a BTC transfer from the low-liquidity side, and a USDC transfer from the high-liquidity side.
        """

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=1.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        arb_order.traded_base_amount_low_liquidity = 0.000095
        arb_order.traded_quote_amount_low_liquidity = 20 # is smaller than minimum amount

        assert self.bot.funds_transfer(arb_order)
        self.assertEqual(arb_order.pending_amount_low_liquidity, arb_order.original_amount)
        self.assertEqual(arb_order.traded_quote_amount_low_liquidity, arb_order.traded_quote_amount_low_liquidity)
        self.assertEqual(arb_order.traded_amount_base_high_liquidity, arb_order.traded_amount_quote_high_liquidity)

    @patch.object(BudaProxy, 'create_lightning_invoice',
                  return_value=test_api_constants.buda_ln_invoice_001)
    @patch.object(BinanceProxy, 'create_withdraw_request',
                  return_value=test_api_constants.binance_withdrawal_response)
    @patch.object(BinanceProxy, 'get_withdraw_history',
                  return_value=test_api_constants.binance_withdrawal_history)
    @patch.object(BudaProxy, 'create_withdraw_request',
                   return_value=test_api_constants.buda_withdrawal_usdc_response)
    @patch.object(BudaProxy, 'get_withdraw_history',
                  return_value=test_api_constants.buda_usdc_withdrawal_history)
    def test_funds_transfer_sell_order(self,
                                       buda_invoice_creation_mock,
                                       binance_withdrawal_response_mock,
                                       binance_withdrawal_history_mock,
                                       buda_withdrawal_response_mock,
                                       buda_withdrawal_history_usdc):
        """
        Suppose we have a SELL_LIMIT scenario with 0.000095 BTC traded on the low-liquidity side.
        We expect a BTC transfer from the high-liquidity side, and a USDC transfer from the low-liquidity side.
        """

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        arb_order.pending_amount_low_liquidity = 10
        arb_order.traded_base_amount_low_liquidity = 0.000095
        arb_order.traded_quote_amount_low_liquidity = 20

        assert self.bot.funds_transfer(arb_order)
        self.assertEqual(arb_order.pending_amount_low_liquidity, arb_order.original_amount)
        self.assertEqual(arb_order.traded_quote_amount_low_liquidity, arb_order.traded_quote_amount_low_liquidity)
        self.assertEqual(arb_order.traded_amount_base_high_liquidity, arb_order.traded_amount_quote_high_liquidity)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response)
    def test_get_price_difference_buy_limit(self, buda_order_book_mock):
        # For a BUY, p_diff = (highest_bid - high_liquidity_price)/high_liquidity_price
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        # Suppose high_liquidity_price=837000.0
        # lowest_ask=836677.14 => p_diff = (837462.23 - 837000)/837000 = ~-0.000551
        p_diff, reference_price = self.bot.get_price_reference(837000.0, arb_order)
        self.assertAlmostEqual(p_diff, -0.00055, places=5)
        self.assertEqual(reference_price, 837000.0)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response)
    def test_get_price_difference_sell_limit(self, buda_order_book_mock):
        # For a BUY, p_diff = (highest_bid - high_liquidity_price)/high_liquidity_price
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        # Suppose high_liquidity_price=837000.0
        # lowest_ask=837597.23 => p_diff = (837597.23 - 837000)/837000 = ~0.000714
        p_diff, reference_price = self.bot.get_price_reference(837000.0, arb_order)
        self.assertAlmostEqual(p_diff, 0.00071, places=5)
        self.assertEqual(reference_price, 837462.23)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response_to_filter)
    def test_get_price_difference_sell_limit_filtered_market(self, buda_order_book_mock):
        """
        SELL_LIMIT case:
        Test an event where the creation of a profitable market order is possible
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=100,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        high_liquidity_price = 99
        # lowest_ask=103 => p_diff = (103 - 99)/99 = ~0.04040
        p_diff, reference_price = self.bot.get_price_reference(high_liquidity_price, arb_order)
        self.assertAlmostEqual(p_diff, 0.04040, places=5)
        self.assertEqual(reference_price, 101)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response_to_filter)
    def test_get_price_difference_buy_limit_filtered_market(self, buda_order_book_mock):
        """
        BUY_LIMIT case:
        Test an event where the creation of a profitable market order is possible
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=100,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        high_liquidity_price = 105
        # Suppose high_liquidity_price=837000.0
        # highest_bid=101 => p_diff = (105 - 101)/101 = ~0.03960
        p_diff, reference_price = self.bot.get_price_reference(high_liquidity_price, arb_order)
        self.assertAlmostEqual(p_diff, 0.03960, places=5)
        self.assertEqual(reference_price, 103)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response_to_filter)
    def test_get_price_difference_sell_limit_filtered(self, buda_order_book_mock):
        """
        SELL_LIMIT case:
        Test an event where the price in the high liquidity exchange lower than the highest bid order
        of the low liquidity exchange, but the price difference in not enough to create a profitable market order.
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=100,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        high_liquidity_price = 100
        highest_bid_price = 101
        # lowest_ask=103 => p_diff = (103 - 99)/99 = ~0.04040
        expected_p_diff = (103 - high_liquidity_price) / high_liquidity_price
        expected_price = highest_bid_price * ((1 + 0.001) / (1 + self.bot.price_diff_threshold))
        p_diff, reference_price = self.bot.get_price_reference(high_liquidity_price, arb_order)
        self.assertEqual(p_diff, expected_p_diff)
        self.assertEqual(reference_price, expected_price)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response_to_filter)
    def test_get_price_difference_buy_limit_filtered(self, buda_order_book_mock):
        """
        BUY_LIMIT case:
        Test an event where the price in the high liquidity exchange bigger than the lowest ask order
        of the low liquidity exchange, but the price difference in not enough to create a profitable market order.
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=100,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        high_liquidity_price = 104
        lowest_ask_price = 103
        # highest_bid=101 => p_diff = (103 - 101)/101 = ~0.04040
        expected_p_diff = (high_liquidity_price - 101) / 101
        expected_price = lowest_ask_price * ((1 - 0.001) / (1 - self.bot.price_diff_threshold))
        p_diff, reference_price = self.bot.get_price_reference(high_liquidity_price, arb_order)
        self.assertEqual(p_diff, expected_p_diff)
        self.assertEqual(reference_price, expected_price)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response_to_filter)
    def test_get_price_difference_sell_limit_filtered_volume(self, buda_order_book_mock):
        """
        SELL_LIMIT case:
        Test an event where the price in the high liquidity exchange lower than the highest bid order
        of the low liquidity exchange, but the price difference in not enough to create a profitable market order.
        Also, the highest bid order does not have a volume representative enough to be considered, so it is ignored.
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=100,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        high_liquidity_price = 100.8
        second_highest_bid_price = 100
        # lowest_ask=103 => p_diff = (103 - 100.8)/100.8 = ~0.04040
        expected_p_diff = (103 - high_liquidity_price) / high_liquidity_price
        expected_price = max([second_highest_bid_price, high_liquidity_price])
        p_diff, reference_price = self.bot.get_price_reference(high_liquidity_price, arb_order)
        self.assertEqual(p_diff, expected_p_diff)
        self.assertEqual(reference_price, expected_price)

    @patch.object(BudaProxy, 'get_order_book',
                  return_value=test_api_constants.buda_order_book_response_to_filter)
    def test_get_price_difference_buy_limit_filtered(self, buda_order_book_mock):
        """
        BUY_LIMIT case:
        Test an event where the price in the high liquidity exchange bigger than the lowest ask order
        of the low liquidity exchange, but the price difference in not enough to create a profitable market order.
        Also, the lowest order does not have a volume representative enough to be considered, so it is ignored.
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=100,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.BUY_LIMIT
        )
        high_liquidity_price = 103.222
        second_lowest_ask_price = 104
        # highest_bid=101 => p_diff = (103 - 101)/101 = ~0.04040
        expected_p_diff = (high_liquidity_price - 101) / 101
        expected_price = min([second_lowest_ask_price, high_liquidity_price])
        p_diff, reference_price = self.bot.get_price_reference(high_liquidity_price, arb_order)
        self.assertEqual(p_diff, expected_p_diff)
        self.assertEqual(reference_price, expected_price)

    def test_arbitrage_order_completion(self):
        """
        Tests different cases of ArbitrageOrder
        """

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=24000.0,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )

        reference_price: float = 100000

        arb_order.traded_quote_amount_low_liquidity = 24000.0
        assert self.bot.arbitrage_order_completion(arb_order, reference_price)

        arb_order.traded_quote_amount_low_liquidity = 24000
        assert self.bot.arbitrage_order_completion(arb_order, reference_price)

        arb_order.traded_quote_amount_low_liquidity = 2400
        assert not self.bot.arbitrage_order_completion(arb_order, reference_price)

    @patch.object(BinanceProxy, 'get_price', return_value=test_api_constants.binance_get_price_response)
    def test_get_latest_high_liquidity_price(self, get_price_binance_mock):
        self.arb_order.base_currency = 'BTC'
        self.arb_order.quote_currency = 'USDC'

        btc_price_high_liq_exchange = self.bot._get_latest_high_liquidity_price(self.arb_order)

        assert isinstance(btc_price_high_liq_exchange, float)
        self.assertEqual(btc_price_high_liq_exchange, 104738.01000000)

    def test_calculate_paid_fee_low_liquidity(self):
        """
        Test the correct calculation of the paid fee.
        It should return the paid fee expressed in tue quote currency of arb_order.
        It tests three scenarios:
        1: paid fee in base currency
        2: paid fee in quote currency
        3: paid fee in a currency different from base and quote
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=15,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        buda_bid_order_state = {
          "id": 1366305465,
          "uuid": "12fe1429-ffd8-40c5-9e53-042565ba67f1",
          "market_id": "BTC-USDC",
          "type": "Bid",
          "state": "canceled",
          "fee_currency": "BTC",
          "limit": [
            "105199.922212",
            "USDC"
          ],
          "amount": [
            "0.00028517",
            "BTC"
          ],
          "original_amount": [
            "0.00028517",
            "BTC"
          ],
          "traded_amount": [
            "0.0",
            "BTC"
          ],
          "total_exchanged": [
            "0.0",
            "USDC"
          ],
          "paid_fee": [
            "1.0",
            "BTC"
          ],
        }
        paid_fee_base_currency, paid_fee_quote_currency = self.bot._calculate_paid_fee_low_liquidity(buda_bid_order_state, arb_order)
        self.assertEqual(1.0, paid_fee_base_currency)
        self.assertEqual(105199.922212, paid_fee_quote_currency)
        buda_bid_order_state["paid_fee"] = ["8.888", "USDC"]
        paid_fee_base_currency, paid_fee_quote_currency = self.bot._calculate_paid_fee_low_liquidity(buda_bid_order_state, arb_order)
        self.assertEqual(8.888 / 105199.922212, paid_fee_base_currency)
        self.assertEqual(8.888, paid_fee_quote_currency)

        buda_bid_order_state["paid_fee"] = ["8.888", "BNB"]
        paid_fee_base_currency, paid_fee_quote_currency = self.bot._calculate_paid_fee_low_liquidity(buda_bid_order_state, arb_order)
        self.assertEqual(0, paid_fee_base_currency)

    def test_calculate_paid_fee_high_liquidity(self):
        """
        Test the correct calculation of the paid fee in the high liquidity exchange.
        It should return the paid fee expressed in tue quote currency of arb_order.
        It tests three scenarios:
        1: paid fee in base currency
        2: paid fee in quote currency
        3: paid fee in a currency different from base and quote
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=15,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        binance_bid_order_state = {
            'symbol': 'BTCUSDC',
            'orderId': 3962637728,
            'orderListId': -1,
            'clientOrderId': 'eWpdt8VN1RZgx0tiqIkFD5',
            'transactTime': 1738333733346,
            'price': '0.00000000',
            'origQty': '0.00014000',
            'executedQty': '0.00014000',
            'origQuoteOrderQty': '0.00000000',
            'cummulativeQuoteQty': '14.64585780',
            'status': 'FILLED',
            'timeInForce': 'GTC',
            'type': 'MARKET',
            'side': 'BUY',
            'workingTime': 1738333733346,
            'fills': [
                {
                    'price': '104613.27000000',
                    'qty': '0.00014000',
                    'commission': '1',
                    'commissionAsset': 'BTC',
                    'tradeId': 133249829
                }
            ],
            'selfTradePreventionMode': 'EXPIRE_MAKER'
        }
        paid_fee_base_currency, paid_fee_quote_currency = self.bot._calculate_paid_fee_high_liquidity(binance_bid_order_state, arb_order)
        self.assertEqual(1.0, paid_fee_base_currency)
        self.assertEqual(104613.27000000, paid_fee_quote_currency)
        binance_bid_order_state["fills"][0]["commission"] = "8.888"
        binance_bid_order_state["fills"][0]["commissionAsset"] = "USDC"
        paid_fee_base_currency, paid_fee_quote_currency = self.bot._calculate_paid_fee_high_liquidity(binance_bid_order_state, arb_order)
        self.assertEqual(8.888 / 104613.27, paid_fee_base_currency)
        self.assertEqual(8.888, paid_fee_quote_currency)

        binance_bid_order_state["fills"][0]["commission"] = "8.888"
        binance_bid_order_state["fills"][0]["commissionAsset"] = "BNB"
        paid_fee_base_currency, paid_fee_quote_currency = self.bot._calculate_paid_fee_high_liquidity(binance_bid_order_state, arb_order)
        self.assertEqual(0, paid_fee_base_currency)

    def test_calculate_real_price_diff(self):
        """
        Test the correct calculation of the real price difference.
        It tests three scenarios:
        1: price difference for a SELL_LIMIT order
        2: price difference for a BUY_LIMIT order
        3: price difference for a non valid order
        """
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=15,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        limit_low_liquidity = 1000
        limit_high_liquidity = 1100
        sell_limit_diff = self.bot._calculate_real_price_diff(arb_order, limit_low_liquidity, limit_high_liquidity)
        self.assertEqual(round(sell_limit_diff, 5), -0.09091)

        arb_order.order_type = OrderType.BUY_LIMIT
        buy_limit_diff = self.bot._calculate_real_price_diff(arb_order, limit_low_liquidity, limit_high_liquidity)
        self.assertEqual(buy_limit_diff, 0.1)

        arb_order.order_type = 'Non_valid_order'
        non_valid_limit_diff = self.bot._calculate_real_price_diff(arb_order, limit_low_liquidity, limit_high_liquidity)
        self.assertEqual(non_valid_limit_diff, 0.0)

    def test_get_low_liquidity_taker_fee(self):
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=15,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        taker_fee = self.bot.get_low_liquidity_taker_fee(arb_order)
        expected_fee = 0.7 / 100
        self.assertEqual(taker_fee, expected_fee)

    # def test_run_arbitrage_flow_sell_limit(self):
    #     """
    #     Test the arbitrage flow, on a first iteration condition
    #     """
    #
    #     arb_order = ArbitrageOrder(
    #         base_currency="BTC",
    #         quote_currency="USDC",
    #         amount=20.0,
    #         original_amount=15,
    #         currency_of_interest=CurrencyOfInterest.QUOTE,
    #         order_type=OrderType.SELL_LIMIT
    #     )
    #     self.bot.run_arbitrage_flow(arb_order=arb_order)

    @patch.object(ArbitrageBot, 'place_sub_orders', return_value=test_a_bot_constans.place_sub_orders_sell_limit_flow_traded)
    @patch.object(BudaProxy, 'batch_cancellation', return_value=test_a_bot_constans.batch_cancellation_sell_limit_flow_traded)
    @patch.object(BudaProxy, 'get_order_states', return_value=test_a_bot_constans.states_sub_orders_sell_limit_flow)
    @patch.object(BinanceProxy, 'new_order', side_effect=Exception('Simulated error in new_order'))
    @patch.object(BudaProxy, 'create_withdraw_request', return_value=test_a_bot_constans.buda_create_withdraw_request_sell_limit_flow_traded)
    @patch.object(BinanceProxy, 'pay_ln_invoice', return_value=test_a_bot_constans.binance_pay_ln_invoice_sell_limit_flow_traded)
    @patch.object(BinanceProxy, 'get_withdraw_history',
                  side_effect=[
                      test_a_bot_constans.binance_get_withdraw_history_sell_limit_flow_traded_1,
                      test_a_bot_constans.binance_get_withdraw_history_sell_limit_flow_traded_2])
    @patch.object(BudaProxy, 'get_withdraw_history',
                  side_effect=[
                      test_a_bot_constans.buda_get_withdraw_history_sell_limit_flow_traded_1,
                      test_a_bot_constans.buda_get_withdraw_history_sell_limit_flow_traded_2])
    def test_run_arbitrage_flow_fail_binance(self,
                                                  mock_buda_place_sub_orders,
                                                  mock_buda_batch_cancellation,
                                                  mock_buda_get_order_states,
                                                  mock_binance_new_order,
                                                  mock_buda_create_withdraw_request,
                                                  mock_binance_pay_ln_invoice,
                                                  mock_binance_get_withdraw_history,
                                                  mock_buda_get_withdraw_history
                                                  ):
        """
        Test the arbitrage flow, on a first iteration condition
        """
        mock_binance_new_order.status_code = 400
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=15,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        self.bot.run_arbitrage_flow(arb_order=arb_order, debug_mode=True)

    @patch("src.arbitrage_bot.arbitrage_bot.logger")
    def test_run_arbitrage_flow_amount_below_min_total(self, mock_logger):
        """
        Test that if place_sub_orders returns an error indicating the order amount is below the minimum,
        run_arbitrage_flow logs the error and exits the loop.
        """

        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=1,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        self.bot.run_arbitrage_flow(arb_order=arb_order, debug_mode=True)
        found_error = False
        for call in mock_logger.error.call_args_list:
            args, kwargs = call
            if "Order amount is below the minimum allowed by the exchange" in args[0]:
                found_error = True
                break
        self.assertTrue(found_error, "Expected error message not found in logger.error calls.")

    def test_get_min_withdrawal_amount_high_liquidity_eth_network(self):
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=15,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        result = self.bot.get_min_withdrawal_quote_amount_high_liquidity("eth", arb_order)
        self.assertEqual(result, 20.0)

    def test_get_min_notional_high_liquidity(self):
        arb_order = ArbitrageOrder(
            base_currency="BTC",
            quote_currency="USDC",
            original_amount=15,
            currency_of_interest=CurrencyOfInterest.QUOTE,
            order_type=OrderType.SELL_LIMIT
        )
        result: float = self.bot.get_min_notional_high_liquidity(arb_order)
        self.assertTrue(isinstance(result, float))
        self.assertEqual(result, 5)
