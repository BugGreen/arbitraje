from unittest.mock import patch, Mock
from src.exchange_api.buda_proxy import BudaProxy


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


from unittest.mock import patch, Mock
from src.exchange_api.buda_proxy import BudaProxy
import pytest

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
