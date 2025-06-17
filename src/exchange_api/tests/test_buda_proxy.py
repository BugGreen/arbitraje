from unittest.mock import patch, Mock
from src.exchange_api.buda_proxy import BudaProxy
import pytest


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
        headers = buda._sign_request(params={}, method=method, path=path, body=body)

    # Assertions
    assert headers["X-SBTC-APIKEY"] == "test_api_key"
    assert headers["X-SBTC-NONCE"] == "1633036800000000"  # Time in microseconds
    assert "X-SBTC-SIGNATURE" in headers
    assert len(headers["X-SBTC-SIGNATURE"]) == 96  # SHA-384 produces 96-character hex


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
def test_create_deposit_address_invalid_coin(mock_post):
    """
    Test the create_deposit_address method with an invalid coin.
    """
    # Arrange
    buda = BudaProxy()

    # Act & Assert
    with pytest.raises(ValueError, match="Lightning Network invoices are only supported for BTC."):
        buda.create_deposit_address(coin="ETH", network="lightning", amount_satoshis=5000)

    mock_post.assert_not_called()


@patch("requests.post")
def test_create_deposit_address_invalid_network(mock_post):
    """
    Test the create_deposit_address method with an invalid network.
    """
    # Arrange
    buda = BudaProxy()

    # Act & Assert
    with pytest.raises(ValueError, match="This method only supports the Lightning Network."):
        buda.create_deposit_address(coin="BTC", network="onchain", amount_satoshis=5000)

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
def test_create_withdraw_request_success(mock_post):
    """
    Test the create_withdraw_request method with a successful response.
    """
    # Arrange
    buda = BudaProxy()
    buda.api_key = "test_api_key"
    buda.api_secret = "test_api_secret"

    expected_response = {
        "id": 123,
        "created_at": "2024-11-01T12:00:00Z",
        "amount": {"amount": "0.01", "currency": "BTC"},
        "currency": "BTC",
        "fee": {"amount": "0.0001", "currency": "BTC"},
        "state": "confirmed",
        "withdrawal_data": {
            "type": "lightning_network_withdrawal_data",
            "payment_request": "lnbc123...",
            "payment_error": None,
        },
    }

    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = expected_response
    mock_post.return_value = mock_response

    # Act
    result = buda.create_withdraw_request(
        coin="BTC",
        payment_request="lnbc123...",
        amount=0.01,
        simulate=True
    )

    # Assert
    assert result == expected_response
    mock_post.assert_called_once_with(
        f"{buda.BASE_URL}{buda.ENDPOINTS['LIGHTNING_WITHDRAWAL']}",
        headers=mock_post.call_args[1]["headers"],  # Authentication headers
        json={
            "amount": 0.01,
            "withdrawal_data": {"payment_request": "lnbc123..."},
            "simulate": True
        }
    )


@patch("requests.post")
def test_create_withdraw_request_invalid_coin(mock_post):
    """
    Test the create_withdraw_request method with an invalid coin.
    """
    # Arrange
    buda = BudaProxy()

    # Act & Assert
    with pytest.raises(ValueError, match="This method only supports Lightning Network withdrawals for BTC."):
        buda.create_withdraw_request(
            coin="ETH", payment_request="lnbc123...", amount=0.01
        )

    mock_post.assert_not_called()


@patch("requests.post")
def test_create_withdraw_request_api_error(mock_post):
    """
    Test the create_withdraw_request method when the API returns an error.
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
        buda.create_withdraw_request(
            coin="BTC", payment_request="lnbc123...", amount=0.01, simulate=False
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