import pytest
from src.exchange_api.binance_proxy import BinanceProxy
from unittest.mock import patch, Mock


def test_binance_proxy_initialization():
    """
    Test the initialization of BinanceProxy.
    """
    with patch('src.exchange_api.binance_proxy.load_api_keys') as mock_load_api_keys:
        mock_load_api_keys.return_value = ('test_api_key', 'test_api_secret')
        binance = BinanceProxy()
        assert binance.api_key == 'test_api_key'
        assert binance.api_secret == 'test_api_secret'


def test_binance_get_coin_info():
    """
    Test the get_coin_info method of BinanceProxy.
    """
    binance = BinanceProxy()
    expected_response = [{"coin": "BTC", "networkList": []}]

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        coin_info = binance.get_coin_info()
        assert coin_info == expected_response
        mock_get.assert_called_once()


def test_binance_supports_lightning_network():
    """
    Test the supports_lightning_network method of BinanceProxy.
    """
    binance = BinanceProxy()
    mock_coin_info = [
        {
            "coin": "BTC",
            "networkList": [
                {"network": "BTC", "withdrawEnable": True},
                {"network": "Lightning", "withdrawEnable": True}
            ]
        }
    ]

    with patch.object(binance, 'get_coin_info', return_value=mock_coin_info):
        assert binance.supports_lightning_network("BTC") == True

    mock_coin_info_no_lightning = [
        {
            "coin": "BTC",
            "networkList": [
                {"network": "BTC", "withdrawEnable": True},
                {"network": "ERC20", "withdrawEnable": False}
            ]
        }
    ]

    with patch.object(binance, 'get_coin_info', return_value=mock_coin_info_no_lightning):
        assert binance.supports_lightning_network("BTC") == False


def test_create_deposit_address():
    """
    Test the create_deposit_address method of BinanceProxy.
    """
    binance = BinanceProxy()

    # Mock the expected API response
    expected_response = {
        "address": "1HPn8Rx2y6nNSfagQBKy27GB99Vbzg89wv",
        "coin": "BTC",
        "tag": "",
        "url": "https://btc.com/1HPn8Rx2y6nNSfagQBKy27GB99Vbzg89wv"
    }

    # Mock the requests.get method
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        # Call the method
        deposit_address = binance.create_deposit_address(coin="BTC", network="BTC")

        # Assertions
        assert deposit_address == expected_response
        mock_get.assert_called_once()
        mock_get.assert_called_with(
            f"{binance.BASE_URL}{binance.ENDPOINTS['DEPOSIT_ADDRESS']}",
            headers={"X-MBX-APIKEY": binance.api_key},
            params=mock_get.call_args[1]["params"]  # Ensure params match the call
        )