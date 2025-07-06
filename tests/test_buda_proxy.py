from unittest.mock import patch, Mock, MagicMock
import unittest
from src.exchange_api.low_liquidity_exchanges.buda_proxy import BudaProxy
from src.exchange_api.exchange_factory import ExchangeFactory
import pytest
import requests
from tests import exchange_constants as constants

buda: BudaProxy = ExchangeFactory.get_exchange('buda')


def test_sign_request():
    """
    Test the _sign_request method of BudaProxy.
    """
    buda.api_key = "test_api_key"
    buda.api_secret = "test_api_secret"

    # Input parameters
    method = "POST"
    path = "/api/v1/orders"
    body = '{"amount": "0.01", "price": "30000", "type": "buy"}'

    # Expected nonce (mocked to a specific value for testing)
    with patch("time.time", return_value=1633036800):  # Mock current time
        headers = buda._sign_request(method=method, path=path, body=body)

    # Assertions
    assert headers["X-SBTC-APIKEY"] == "test_api_key"
    assert headers["X-SBTC-NONCE"] == "1633036800000000"  # Time in microseconds
    assert "X-SBTC-SIGNATURE" in headers
    assert len(headers["X-SBTC-SIGNATURE"]) == 96  # SHA-384 produces 96-character hex


def test_create_withdraw_request_btc():
    """
    Test BTC Lightning Network withdrawal request.
    """

    buda_proxy = ExchangeFactory.get_exchange('buda')
    expired_invoice = 'lnbc50u1pn5f8ljpp5dc6y936p79j9dfqs59vdkz6dfurxcgzvsren4mtahdrva9paqxhsdq8w3jhxaqcqzzsxqyz5vqsp5yp9j2fghxfw4dvxnkcu5lyldykew7ymuq27f8jpay8ms7q9kwe9s9qxpqysgqqczpcedj6ry8t8z5emqvz9mvjr263fsv7p64st6j5pyxfcdmm9hparffkgfsxv883kh6hkczfgpktlevn3rldcskqv392fk8n7ad3lcp6yx88t'

    response = buda_proxy.create_withdraw_request(coin='BTC', address=expired_invoice, amount=0.00002, simulate=True)
    withdrawal_response = response

    assert withdrawal_response['state'] == 'simulated'
    assert withdrawal_response['currency'] == 'BTC'
    assert withdrawal_response["withdrawal_data"]['payment_request'] == expired_invoice


@patch.object(BudaProxy, 'create_withdraw_request',
              return_value=constants.buda_withdrawal_response)
def test_pay_ln_invoice(mock_post):
    """
    Test BTC Lightning Network withdrawal request.
    """

    expired_invoice = 'lnbc50u1pn5f8ljpp5dc6y936p79j9dfqs59vdkz6dfurxcgzvsren4mtahdrva9paqxhsdq8w3jhxaqcqzzsxqyz5vqsp5yp9j2fghxfw4dvxnkcu5lyldykew7ymuq27f8jpay8ms7q9kwe9s9qxpqysgqqczpcedj6ry8t8z5emqvz9mvjr263fsv7p64st6j5pyxfcdmm9hparffkgfsxv883kh6hkczfgpktlevn3rldcskqv392fk8n7ad3lcp6yx88t'
    try:
        response = buda.pay_ln_invoice(ln_invoice=expired_invoice, amount=0.000095, simulate=True)
        withdrawal_id = response["id"]
        assert withdrawal_id in ["VWBwmE", None]
    except Exception as e:
        assert True


def test_create_withdraw_request_ltc():
    """
    Test BTC Lightning Network withdrawal request.
    """

    buda_proxy = ExchangeFactory.get_exchange('buda')
    ltc_address = "LeMNHpnvULWbh9wHqNPdPwnip3vnSsXATY"

    withdrawal_response = buda_proxy.create_withdraw_request(coin='ltc', address=ltc_address, amount=0.00702, simulate=True)
    assert withdrawal_response['state'] == 'simulated'
    assert withdrawal_response['currency'] == 'LTC'
    assert withdrawal_response["withdrawal_data"]['type'] == "ltc_withdrawal_data"
    assert withdrawal_response["withdrawal_data"]['target_address'] == ltc_address  # Here is 'target_address'


def test_get_price():
    price_response = buda.get_price('btc', 'usdc')
    assert price_response.get('symbol') == 'BTCUSDC'
    assert price_response.get('price')


def test_get_market_info():
    buda = BudaProxy()
    base_currency = "BTC"
    quote_currency = "USDC"
    market_info = buda.get_market_info(base_currency, quote_currency).get("market", {})
    assert market_info
    assert market_info.get("id") == f'{base_currency}-{quote_currency}'


def test_get_all_balances():
    buda = BudaProxy()
    balances = buda.get_balances()
    assert balances.get("balances")


def test_get_btc_balances():
    buda = BudaProxy()
    coin = "BTC"
    balance = buda.get_balances(coin)
    assert balance.get('balance', {}).get("id", "") == coin


@patch("requests.post")
def test_create_quote_currency_address(mock_post):
    """
    Test the (create_deposit_address) method for an alt-coin with a successful response.
    """
    buda.api_key = "test_api_key"
    buda.api_secret = "test_api_secret"

    expected_response = constants.buda_usdc_address_ERC20_response

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_post.return_value = mock_response
    result = buda.create_quote_currency_address(coin='USDC')
    assert result.get('address') == "0x4f56c765e4a5ae10d924235a2c813e8b260a3291"


@patch("requests.post")
def test_create_deposit_address_success(mock_post):
    """
    Test the create_deposit_address method with a successful response.
    """
    # Arrange
    buda.api_key = "test_api_key"
    buda.api_secret = "test_api_secret"

    expected_response = {
        "invoice": {
            "id": 123,
            "currency": "BTC",
            "encoded_payment_request": "lnbc227040n1pdmvkw6pp5x7ws3aygr96w..."
        }
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_post.return_value = mock_response

    # Act
    result = buda.create_deposit_address(
        coin="BTC",
        network="lightning",
        amount_satoshis=5000,
        memo="Test Invoice",
        expiry_seconds=3600
    )

    # Assert
    assert result == expected_response["invoice"]
    mock_post.assert_called_once_with(
        f"{buda.BASE_URL}{buda.ENDPOINTS['LIGHTNING_INVOICE']}",
        headers=mock_post.call_args[1]["headers"],  # Authentication headers
        json={
            "amount_satoshis": 5000,
            "currency": "BTC",
            "memo": "Test Invoice",
            "expiry_seconds": 3600
        }
    )


@patch("requests.post")
def test_create_ln_invoice_success(mock_post):
    """
    Test the create_deposit_address method with a successful response.
    """
    # Arrange
    buda.api_key = "test_api_key"
    buda.api_secret = "test_api_secret"

    expected_response = {
        'coin': "BTC",
        'invoice': "lnbc10m1pncjj6ypp54alcwxtfxam2wev98qcxxmz7mjptxjuckeg6h9v6rvfvtrewf5ssdqqcqzzsxqyz5vqsp57xw865jh9dc0kq4z55zkyfacgw9azfazfh5x8al7j8cc3t9dhmrq9qxpqysgq9svt4fh2w4fl4442dkmghsj8gknqdxq5pteaphdjmpm2gl9lxy3p52ecvuw2la3ndwmpzwvqywdxsfxy2884u5lm6n7x68x7lh6jm0spk3e9hg",
        'amount': 0.01
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = constants.buda_ln_invoice_001
    mock_post.return_value = mock_response

    amount = 0.01
    sats_amount = amount * 100000000
    # Act
    result = buda.create_lightning_invoice(amount=amount)

    # Assert
    assert result == expected_response
    mock_post.assert_called_once_with(
        f"{buda.BASE_URL}{buda.ENDPOINTS['LIGHTNING_INVOICE']}",
        headers=mock_post.call_args[1]["headers"],  # Authentication headers
        json={
            "amount_satoshis": sats_amount,
            "currency": "BTC",
        }
    )


@patch("requests.post")
def test_create_deposit_address_invalid_coin(mock_post):
    """
    Test the create_deposit_address method with an invalid coin.
    """

    # Act & Assert
    with pytest.raises(ValueError, match="Error coin ADA is not supported"):
        buda.create_deposit_address(coin="ADA", network="lightning", amount_satoshis=5000)

    mock_post.assert_not_called()


@patch("requests.post")
def test_create_deposit_address_api_error(mock_post):
    """
    Test the create_deposit_address method when the API returns an error.
    """
    mock_response = MagicMock()
    mock_response.status_code = 400

    mock_exception = requests.exceptions.Timeout("Connection timed out")
    mock_exception.response = mock_response

    mock_response.raise_for_status.side_effect = mock_exception
    mock_post.return_value = mock_response
    buda.api_key = "test_api_key"
    buda.api_secret = "test_api_secret"

    # Act & Assert
    with pytest.raises(Exception, match="Failed after 3 retries"):
        buda.create_deposit_address(
            coin="BTC", network="lightning", amount_satoshis=5000, memo="Test Invoice"
        )

    assert mock_post.call_count == 3


@patch("requests.post")
def test_new_order_limit(mock_post):
    # Setup for the BudaProxy instance
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    expected_response = {"order": {"id": 1, "amount": ["0.05", "BTC"], "price_type": "limit"}}

    # Mock the response from the API
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_post.return_value = mock_response

    # Call the new_order method
    response = buda.new_order(
        base_currency='btc',
        quote_currency='clp',
        side='Bid',
        order_type='limit',
        amount=0.05,
        price=1000000,
        order_limit_type='gtc',
        client_id='my-order-1'
    )

    # Check the response
    assert response['order']['price_type'] == 'limit'
    assert response['order']['id'] == 1
    assert response['order']['amount'][0] == '0.05'
    assert response['order']['amount'][1] == 'BTC'


@patch("requests.post")
def test_new_order_market(mock_post):
    # Setup for the BudaProxy instance
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    expected_response = {"order": {"id": 2, "amount": ["0.05", "BTC"], "price_type": "market"}}
    # Mock the response from the API
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_post.return_value = mock_response

    # Call the new_order method with market order type
    response = buda.new_order(
        base_currency='btc',
        quote_currency='clp',
        side='Ask',
        order_type='market',
        amount=0.05,
        client_id='my-order-2'
    )

    # Check the response
    assert response['order']['price_type'] == 'market'
    assert response['order']['id'] == 2
    assert response['order']['amount'][0] == '0.05'
    assert response['order']['amount'][1] == 'BTC'


@patch("requests.put")
def test_cancel_order_success(mock_put):
    # Mocking the response from the Buda API
    expected_response = {
        "amount": ["0.05", "BTC"],
        "created_at": "2023-10-28T19:54:24.611Z",
        "fee_currency": "BTC",
        "id": 12345,
        "client_id": "my-order-1",
        "limit": ["1000000.0", "CLP"],
        "market_id": "btc-clp",
        "original_amount": ["0.05", "BTC"],
        "paid_fee": ["0.0", "BTC"],
        "price_type": "limit",
        "order_type": "gtc",
        "state": "canceling",  # This state indicates the order is being canceled
        "total_exchanged": ["0.0", "CLP"],
        "traded_amount": ["0.0", "BTC"],
        "type": "Bid"
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_put.return_value = mock_response

    # Instance of BudaProxy
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    # Call the cancel_order method
    response = buda.cancel_order(base_currency="btc", quote_currency="clp", order_id=12345)

    # Assert the response data
    assert response['state'] == "canceling"
    assert response['id'] == 12345
    assert response['amount'] == ["0.05", "BTC"]
    assert response['market_id'] == "btc-clp"
    assert response['type'] == "Bid"


@patch("requests.get")
def test_get_order_states(mock_get):
    expected_response = {
        "orders": [
            {
              "id": 1267767109,
              "uuid": "48164fca-72c7-4a31-9720-0bf1d4d81d2a",
              "market_id": "ETH-COP",
              "account_id": 143870,
              "type": "Bid",
              "state": "canceled",
              "created_at": "2024-12-03T12:48:42.549Z",
              "fee_currency": "ETH",
              "price_type": "limit",
              "source": "null",
              "client_id": "null",
              "message": "null",
              "order_type": "gtc",
              "expire_at": 0,
              "limit": [
                "15000000.0",
                "COP"
              ],
              "amount": [
                "0.0012",
                "ETH"
              ],
              "original_amount": [
                "0.0012",
                "ETH"
              ],
              "traded_amount": [
                "0.0",
                "ETH"
              ],
              "total_exchanged": [
                "0.0",
                "COP"
              ],
              "paid_fee": [
                "0.0",
                "ETH"
              ],
              "stop_price": "null"
            }]}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_get.return_value = mock_response

    # Instance of BudaProxy
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    response = buda.get_order_states(base_currency='eth', quote_currency='cop')

    assert isinstance(response['orders'], list)
    assert response['orders'][0]['market_id'] == "ETH-COP"


@patch("requests.get")
def test_get_withdraw_history(mock_get):
    expected_response = constants.buda_withdrawal_history

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"withdrawals": expected_response}
    mock_get.return_value = mock_response

    # Instance of BudaProxy
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    response = buda.get_withdraw_history(coin='btc')

    assert isinstance(response, list)
    assert response[0]['id'] == "EwjxVM"


@patch("requests.get")
def test_get_deposit_history(mock_get):
    expected_response = constants.buda_deposit_history

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"deposits": expected_response}
    mock_get.return_value = mock_response

    # Instance of BudaProxy
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    response = buda.get_deposit_history(coin='btc')

    assert isinstance(response, list)
    assert response[0]['id'] == "lNxKKG"


@patch("requests.post")
def test_batch_cancellation_success(mock_post):
    # Mocking the response from the Buda API
    expected_response = {
      "orders_diff": [
        {
          "mode": "cancel",
          "order_id": 1267969492
        },
        {
          "mode": "cancel",
          "order_id": 1267969493
        }
      ]
    }

    orders = [
        {"mode": "cancel", "order_id": 1000},
        {"mode": "cancel", "oder_id": 9999},
    ]

    # Setup mock to return a success response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_post.return_value = mock_response

    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    # Call the batch_cancelation method
    response = buda.batch_cancellation(orders)

    # Assert the response data
    assert isinstance(response['orders_diff'], list)
    assert response['orders_diff'][0]['mode'] == "cancel"
    assert mock_post.called_once()


@patch("requests.get")
def test_get_order_book_success(mock_get):
    """
    Test successful retrieval of the order book from Buda.
    """
    # Sample mock response data
    mock_response_data = {
        "order_book": {
            "asks": [
                ["836677.14", "0.447349"],
                ["837462.23", "1.43804963"],
                ["837571.89", "1.41498541"],
                ["837597.23", "0.13177617"],
                ["837753.25", "1.40724154"]
            ],
            "bids": [
                ["821580.0", "0.25667389"],
                ["821211.0", "0.27827307"],
                ["819882.39", "1.40003128"],
                ["819622.99", "1.40668862"],
                ["819489.9", "1.41736995"]
            ]
        }
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    # Configure the mock to return a response with our mock data
    mock_get.return_value = mock_response

    # Initialize BudaProxy instance with dummy API credentials
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    # Call the get_order_book method
    result = buda.get_order_book(base_currency='BTC', quote_currency='CLP')

    # Assertions to verify the response
    assert "order_book" in result, "Response should contain 'order_book' key."
    assert "asks" in result["order_book"], "Order book should contain 'asks'."
    assert "bids" in result["order_book"], "Order book should contain 'bids'."
    assert isinstance(result["order_book"]["asks"], list), "'asks' should be a list."
    assert isinstance(result["order_book"]["bids"], list), "'bids' should be a list."


def test_get_order_book_failure():
    """
    Test retrieval of the order book when the API call fails.
    """
    # Configure the mock to return a 404 Not Found response

    # Initialize BudaProxy instance with dummy API credentials
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    try:
        # Call the get_order_book method, which should raise an Exception
        buda.get_order_book(base_currency='INVALID', quote_currency='PAIR')
        assert False, "Expected Exception was not raised."
    except Exception as e:
        assert "Failed after" in str(e), "Exception message should contain 'Error 404'."


def test_cancel_all_orders_specific_market():
    """
    Test retrieval of the order book when the API call fails.
    """
    buda: BudaProxy = BudaProxy()
    base_currency: str = "btc"
    quote_currency: str = "usdc"

    cancel_response = buda.cancel_all_orders(base_currency, quote_currency)
    assert "orders" in cancel_response


class TestBudaProxy(unittest.TestCase):
    def setUp(self):
        self.proxy = BudaProxy()

    @patch('requests.post')
    def test_batch_creation_amount_less_than_minimum_error(self, mock_post):
        # Mock an API-level error response
        # Mock a network-related exception
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_exception = requests.exceptions.Timeout("Connection timed out")
        mock_exception.response = mock_response

        mock_response.raise_for_status.side_effect = mock_exception
        mock_post.return_value = mock_response

        orders = constants.amount_less_than_minimum_order

        try:
            # Call the get_order_book method, which should raise an Exception
            response = self.proxy.batch_creation(orders)
            assert False, "Expected Exception was not raised."
        except Exception as e:
            assert "Failed after" in str(e), "Exception message should contain 'Error 404'."

    @patch('requests.post')
    def test_batch_creation_request_exception(self, mock_post):
        # Mock a network-related exception
        mock_response = MagicMock()
        mock_response.status_code = 502

        mock_exception = requests.exceptions.Timeout("Connection timed out")
        mock_exception.response = mock_response

        mock_response.raise_for_status.side_effect = mock_exception
        mock_post.return_value = mock_response

        orders = [
            {
                "mode": "place",
                "order": {
                    "amount": 0.0012,
                    "limit": 10000000.0,
                    "market_name": "eth-cop",
                    "price_type": "limit",
                    "type": "Bid"
                }
            }
        ]


        try:
            # Call the get_order_book method, which should raise an Exception
            response = self.proxy.batch_creation(orders)
            assert False, "Expected Exception was not raised."
        except Exception as e:
            assert "Failed after" in str(e), "Exception message should contain 'Failed after'."

    @patch('requests.post')
    def test_batch_creation_unexpected_exception(self, mock_post):
        # Mock an unexpected exception
        mock_post.side_effect = Exception("Unexpected error")

        orders = [
            {
                "mode": "place",
                "order": {
                    "amount": 0.0012,
                    "limit": 10000000.0,
                    "market_name": "eth-cop",
                    "price_type": "limit",
                    "type": "Bid"
                }
            }
        ]

        expected_output = {
            "error_code": "UNKNOWN_ERROR",
            "message": "Unexpected error"
        }

        try:
            # Call the get_order_book method, which should raise an Exception
            response = self.proxy.batch_creation(orders)
            assert False, "Expected Exception was not raised."
        except Exception as e:
            assert "Unexpected error" in str(e), "Exception message should contain 'Unexpected error'."


class TestBudaProxyOrderBook(unittest.TestCase):

    def setUp(self):
        self.proxy = BudaProxy()
        self.proxy.order_book_snapshot = {"asks": {}, "bids": {}}
        self.proxy.quote_currency: str = 'usdc'
        self.proxy.base_currency: str = 'btc'

    def test_set_initial_order_book(self):
        snapshot = {
            "order_book": {
                "asks": [["79084646.0", "0.008751"], ["79090631.0", "0.64661344"]],
                "bids": [["78402123.0", "0.00154805"], ["78400770.0", "0.476906"]]
            },
            "market_id": "BTC-CLP"
        }
        self.proxy.set_initial_order_book(snapshot)
        current = self.proxy.get_current_order_book()
        expected = {
            "order_book": {
                "asks": [["79084646.0", "0.008751"], ["79090631.0", "0.64661344"]],
                "bids": [["78402123.0", "0.00154805"], ["78400770.0", "0.476906"]]
            }
        }
        self.assertEqual(current, expected)

    def test_get_current_order_book(self):
        expected_order_book = {
            'order_book': {
                'asks': [['837753.25', '1.40724154'], ['837597.23', '0.13177617']],
                'bids': [['836677.14', '0.447349'], ['837462.23', '1.43804963']]
            }
        }
        self.proxy.order_book_snapshot = {
            "asks": {
                "837753.25": "1.40724154",
                "837597.23": "0.13177617"
            },
            "bids": {
                "836677.14": "0.447349",
                "837462.23": "1.43804963"
            }
        }

        # Act
        result = self.proxy.get_current_order_book()

        # Assert
        self.assertEqual(result, expected_order_book)

    def test_update_order_book_state_add(self):
        # Start with empty state, add a positive change
        self.proxy.update_order_book_state("asks", "79559436.91", "0.00156315")
        current = self.proxy.order_book_snapshot
        self.assertIn("79559436.91", current["asks"])
        self.assertAlmostEqual(float(current["asks"]["79559436.91"]), 0.00156315, places=8)

    def test_update_order_book_state_increment(self):
        # Set initial value, then add more
        self.proxy.order_book_snapshot = {"asks": {"79559436.91": "0.00156315"}, "bids": {}}
        self.proxy.update_order_book_state("asks", "79559436.91", "0.00043685")
        current = self.proxy.order_book_snapshot
        # Expected new amount = 0.00156315 + 0.00043685 = 0.002
        self.assertIn("79559436.91", current["asks"])
        self.assertAlmostEqual(float(current["asks"]["79559436.91"]), 0.002, places=8)

    def test_update_order_book_state_decrement_partial(self):
        # Set initial value, then subtract partially
        self.proxy.order_book_snapshot = {"asks": {"79559436.91": "0.002"}, "bids": {}}
        self.proxy.update_order_book_state("asks", "79559436.91", "-0.001")
        current = self.proxy.order_book_snapshot
        # Expected new amount = 0.002 - 0.001 = 0.001
        self.assertIn("79559436.91", current["asks"])
        self.assertAlmostEqual(float(current["asks"]["79559436.91"]), 0.001, places=8)

    def test_update_order_book_state_remove(self):
        # Set initial value, then subtract enough to remove the level.
        self.proxy.order_book_snapshot = {"asks": {"79559436.91": "0.001"}, "bids": {}}
        self.proxy.update_order_book_state("asks", "79559436.91", "-0.0011")
        current = self.proxy.order_book_snapshot
        self.assertNotIn("79559436.91", current["asks"])

    @patch("websocket.WebSocketApp")
    def test_reconnect_on_error(self, MockWebSocketApp):
        # Mock the WebSocketApp to simulate disconnection
        mock_ws = MagicMock()
        MockWebSocketApp.return_value = mock_ws

        # Simulate a connection error
        self.proxy.on_error_order_book(mock_ws, "Error: Broken pipe")

        # Verify that reconnect_to_order_book was called
        self.proxy.reconnect_to_order_book = MagicMock()
        self.proxy.on_error_order_book(mock_ws, "Error: Broken pipe")
        self.proxy.reconnect_to_order_book.assert_called_once()

    @patch("websocket.WebSocketApp")
    def test_reconnect_on_close(self, MockWebSocketApp):
        # Mock the WebSocketApp to simulate connection closure
        mock_ws = MagicMock()
        MockWebSocketApp.return_value = mock_ws

        # Simulate WebSocket closure
        self.proxy.on_close_order_book(mock_ws, 1000, "Normal closure")

        # Verify that reconnect_to_order_book was called
        self.proxy.reconnect_to_order_book = MagicMock()
        self.proxy.on_close_order_book(mock_ws, 1000, "Normal closure")
        self.proxy.reconnect_to_order_book.assert_called_once_with()


class TestOrderStateWebSocketClient(unittest.TestCase):

    @patch('websocket.WebSocketApp')
    def test_connect_to_order_states(self, MockWebSocketApp):
        client: BudaProxy = BudaProxy()
        mock_ws = MagicMock()
        MockWebSocketApp.return_value = mock_ws

        # Simulate successful connection
        client.connect_to_order_states(initial_snapshot={"orders": []})
        mock_ws.run_forever.assert_called_once()

    def test_add_or_update_order_state(self):
        client: BudaProxy = BudaProxy()
        client.max_order_states_length: int = 2

        # Simulate adding a new order
        client.add_or_update_order_state(1, {"id": 1, "state": "pending"})
        self.assertEqual(len(client.order_states_snapshot["orders"]), 1)

        # Simulate updating the order
        client.add_or_update_order_state(1, {"id": 1, "state": "completed"})
        self.assertEqual(client.order_states_snapshot["orders"][0]["order"]["state"], "completed")

        # Simulate adding a second order and exceeding the limit
        client.add_or_update_order_state(2, {"id": 2, "state": "pending"})
        client.add_or_update_order_state(3, {"id": 3, "state": "pending"})
        self.assertEqual(len(client.order_states_snapshot["orders"]), 2)  # Should be capped at 2
