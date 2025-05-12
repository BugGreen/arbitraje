from unittest.mock import patch, Mock, MagicMock
import unittest
from src.exchange_api.buda_proxy import BudaProxy
from src.exchange_api.exchange_factory import ExchangeFactory
import pytest
import requests
from src.exchange_api.tests import constants


def test_sign_request():
    """
    Test the _sign_request method of BudaProxy.
    """
    buda = BudaProxy()
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

    buda_proxy = ExchangeFactory.get_exchange('buda')
    expired_invoice = 'lnbc50u1pn5f8ljpp5dc6y936p79j9dfqs59vdkz6dfurxcgzvsren4mtahdrva9paqxhsdq8w3jhxaqcqzzsxqyz5vqsp5yp9j2fghxfw4dvxnkcu5lyldykew7ymuq27f8jpay8ms7q9kwe9s9qxpqysgqqczpcedj6ry8t8z5emqvz9mvjr263fsv7p64st6j5pyxfcdmm9hparffkgfsxv883kh6hkczfgpktlevn3rldcskqv392fk8n7ad3lcp6yx88t'

    response = buda_proxy.pay_ln_invoice(ln_invoice=expired_invoice, amount=0.000095)
    withdrawal_id = response["id"]

    assert withdrawal_id == "VWBwmE"


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
    binance = BudaProxy()
    price_response = binance.get_price('btc', 'usdc')
    assert price_response.get('symbol') == 'BTCUSDC'
    assert price_response.get('price')


@patch("requests.post")
def test_create_quote_currency_address(mock_post):
    """
    Test the create_deposit_address method for an alt-coin with a successful response.
    """
    buda = BudaProxy()
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
    buda = BudaProxy()
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
    buda = BudaProxy()
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
    # Arrange
    buda = BudaProxy()

    # Act & Assert
    with pytest.raises(ValueError, match="Error coin ADA is not supported"):
        buda.create_deposit_address(coin="ADA", network="lightning", amount_satoshis=5000)

    mock_post.assert_not_called()


@patch("requests.post")
def test_create_deposit_address_api_error(mock_post):
    """
    Test the create_deposit_address method when the API returns an error.
    """
    # Arrange
    buda = BudaProxy()
    buda.api_key = "test_api_key"
    buda.api_secret = "test_api_secret"

    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = '{"error": "Invalid request"}'
    mock_post.return_value = mock_response

    # Act & Assert
    with pytest.raises(Exception, match="Error 400: {\"error\": \"Invalid request\"}"):
        buda.create_deposit_address(
            coin="BTC", network="lightning", amount_satoshis=5000, memo="Test Invoice"
        )

    mock_post.assert_called_once()


@patch("requests.post")
def test_new_order_limit(mock_post):
    # Setup for the BudaProxy instance
    buda = BudaProxy()
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
    buda = BudaProxy()
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
    buda = BudaProxy()
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
    buda = BudaProxy()
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
    buda = BudaProxy()
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
    buda = BudaProxy()
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

    buda = BudaProxy()
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
    buda = BudaProxy()
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    # Call the get_order_book method
    result = buda.get_order_book(base_currency='BTC', quote_currency='CLP')

    # Assertions to verify the response
    assert "order_book" in result, "Response should contain 'order_book' key."
    assert "asks" in result["order_book"], "Order book should contain 'asks'."
    assert "bids" in result["order_book"], "Order book should contain 'bids'."
    assert isinstance(result["order_book"]["asks"], list), "'asks' should be a list."
    assert isinstance(result["order_book"]["bids"], list), "'bids' should be a list."


@patch("requests.get")
def test_get_order_book_failure(mock_get):
    """
    Test retrieval of the order book when the API call fails.
    """
    # Configure the mock to return a 404 Not Found response
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.return_value.text = "Market not found."
    mock_get.return_value = mock_response

    # Initialize BudaProxy instance with dummy API credentials
    buda = BudaProxy()
    buda.api_key, buda.api_secret = 'test_api_key', 'test_api_secret'

    try:
        # Call the get_order_book method, which should raise an Exception
        buda.get_order_book(base_currency='INVALID', quote_currency='PAIR')
        assert False, "Expected Exception was not raised."
    except Exception as e:
        assert "Error 404" in str(e), "Exception message should contain 'Error 404'."


class TestBudaProxy(unittest.TestCase):
    def setUp(self):
        self.proxy = BudaProxy()

    @patch('requests.post')
    def test_batch_creation_success(self, mock_post) -> None:
        # Mock a successful API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = constants.successful_batch_order_mock_response

        mock_post.return_value = mock_response

        orders = constants.successful_batch_order

        expected_output = constants.expected_successful_batch_order_response

        response = self.proxy.batch_creation(orders)
        self.assertEqual(response, expected_output)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_batch_creation_partial_success(self, mock_post) -> None:
        """
        An example is when one of the suborder of the batch attempts to execute an amount that is not currently
        available.

        :param mock_post:
        :return:
        """
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = constants.successful_batch_order_mock_response
        mock_post.return_value = mock_response

        orders = constants.partial_successful_batch_order

        expected_output = constants.expected_successful_batch_order_response

        response = self.proxy.batch_creation(orders)
        self.assertEqual(response, expected_output)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_batch_creation_amount_less_than_minimum_error(self, mock_post):
        # Mock an API-level error response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = \
            requests.exceptions.HTTPError("EXCHANGE_API_ERROR_invalid_record")
        mock_response.status_code = 422
        mock_response.json.return_value = constants.amount_less_than_minimum_order_mock_response
        mock_post.return_value = mock_response

        orders = constants.amount_less_than_minimum_order

        expected_output = constants.expected_amount_less_than_minimum_response

        response = self.proxy.batch_creation(orders)
        self.assertEqual(response, expected_output)
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_batch_creation_request_exception(self, mock_post):
        # Mock a network-related exception
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

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
            "error_code": "REQUEST_EXCEPTION",
            "message": "Connection timed out"
        }

        response = self.proxy.batch_creation(orders)
        self.assertEqual(response, expected_output)
        mock_post.assert_called_once()

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

        response = self.proxy.batch_creation(orders)
        self.assertEqual(response, expected_output)
        mock_post.assert_called_once()
