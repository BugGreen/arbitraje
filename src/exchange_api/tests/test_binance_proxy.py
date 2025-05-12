from src.exchange_api.binance_proxy import BinanceProxy
from src.exchange_api.tests import constants
from unittest.mock import patch, Mock
from json import dumps as jprint


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


@patch.object(BinanceProxy, "_validate_deposit_availability", return_value=True)
def test_create_deposit_address(deposit_validation_mock):
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


@patch.object(BinanceProxy, "_validate_deposit_availability", return_value=True)
def test_create_ln_invoice(deposit_validation_mock):
    """
    Test the create_deposit_address method of BinanceProxy.
    """
    binance = BinanceProxy()

    # Mock the expected API response
    expected_response = {
        'coin': "BTC",
        'invoice': "lnbc10m1pncjjq2pp5xr8w2ze0es7atjwkzaqzxtc9plx7dgywu9kppynys49c6dewx80qdqqcqzysxqrrsssp5sgj026j0znjd5a92zadhf73qmyl6synu6ch8zjuxznuqmqyymfqq9qxpqysgqres705w8el7g2s6u5629hylc9g00p822kyflsh7jm5cfn745qkz894djv59psejw4w5rf4jq5pgy74cfudtnq2e9aj37gmeullam6vspr43m7j",
        'amount': 0.01
    }

    # Mock the requests.get method
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = constants.binance_ln_invoice_001
        mock_get.return_value = mock_response

        # Call the method
        deposit_address = binance.create_lightning_invoice(amount=0.01)

        # Assertions
        assert deposit_address == expected_response
        mock_get.assert_called_once()
        mock_get.assert_called_with(
            f"{binance.BASE_URL}{binance.ENDPOINTS['DEPOSIT_ADDRESS']}",
            headers={"X-MBX-APIKEY": binance.api_key},
            params=mock_get.call_args[1]["params"]  # Ensure params match the call
        )


def test_create_quote_currency_address():
    """
    Test the create_deposit_address method for an alt-coin with a successful response.
    """
    binance = BinanceProxy()
    result = binance.create_quote_currency_address(coin='USDC', network="ETH")
    assert result.get('address') == "0xc49cc35273f59ba0abec3bf6d895ba15d3a6027b"


def test_create_withdraw_request():
    """
    Test the create_withdraw_request method of BinanceProxy.
    """
    binance = BinanceProxy()

    # Mock the expected API response
    expected_response = {"id": "7213fea8e94b4a5593d507237e5a555b"}

    # Mock the requests.post method
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        # Call the method
        withdraw_request = binance.create_withdraw_request(
            coin="BTC", address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", amount=0.01
        )

        # Assertions
        assert withdraw_request == expected_response
        mock_post.assert_called_once()
        mock_post.assert_called_with(
            f"{binance.BASE_URL}{binance.ENDPOINTS['WITHDRAW_REQUEST']}",
            headers={"X-MBX-APIKEY": binance.api_key},
            params=mock_post.call_args[1]["params"]  # Ensures parameters match
        )


def test_get_price():
    binance = BinanceProxy()
    price_response = binance.get_price('btc', 'usdc')
    assert price_response.get('symbol') == 'BTCUSDC'
    assert price_response.get('price')

@patch("requests.post")
def test_new_order_success(mock_post):

    # Setup the Binance instance or class
    binance = BinanceProxy()

    binance.api_key = "test_api_key"
    binance.api_secret = "test_api_secret"

    # Sample order parameters
    base_currency = 'BTC'
    quote_currency = 'USDT'
    symbol = base_currency + quote_currency
    side = 'BUY'
    order_type = 'LIMIT'
    price = 90000
    quantity = 10
    time_in_force = 'GTC'

    # Mock response from Binance API
    expected_response = {
        "symbol": symbol,
        "orderId": 12345678,
        "clientOrderId": "unique_client_id",
        "transactTime": 1637742499000,
        "price": str(price),
        "origQty": str(quantity),
        "executedQty": '0',
        "status": 'NEW',
        "side": side,
        "type": order_type,
        "timeInForce": time_in_force
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response
    mock_post.return_value = mock_response


    # Call the new_order function
    response = binance.new_order(
        base_currency=base_currency,
        quote_currency=quote_currency,
        side=side,
        order_type=order_type,
        price=price,
        quantity=quantity,
        time_in_force=time_in_force
    )
    print(jprint(response, indent=2))

    # Test if the response contains the expected values
    assert response["symbol"] == symbol
    assert response["side"] == side
    assert response["type"] == order_type
    assert float(response["price"]) == price
    assert float(response["origQty"]) == quantity
    assert response["status"] == "NEW"
    assert response["timeInForce"] == time_in_force

    # Ensure the API was called correctly
    mock_post.assert_called_once()


@patch("requests.post")
def test_new_order_market_success(mock_post):

    # Set up the Binance instance or class
    binance = BinanceProxy()

    binance.api_key = "test_api_key"
    binance.api_secret = "test_api_secret"

    # Sample order parameters
    base_currency = 'BTC'
    quote_currency = 'USDC'
    symbol = base_currency + quote_currency
    side = 'BUY'
    order_type = 'MARKET'
    quote_order_qty = 9

    # Mock response from Binance API

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = constants.binance_successful_market_order_mock_response
    mock_post.return_value = mock_response

    # Call the new_order function for a `MAKER` type order
    response = binance.new_order(base_currency=base_currency,
                                 quote_currency=quote_currency,
                                 side=side,
                                 order_type=order_type,
                                 quote_order_qty=quote_order_qty)

    # Test if the response contains the expected values
    assert response["symbol"] == symbol
    assert response["side"] == side
    assert response["type"] == order_type
    assert response["origQuoteOrderQty"] == f"{quote_order_qty}.00000000"
    assert response["status"] == "FILLED"

    # Ensure the API was called correctly
    mock_post.assert_called_once()


@patch("requests.post")
def test_new_sell_order_market_success(mock_post):

    # This market order is created using quantity instead of quote_order_qty
    binance = BinanceProxy()

    binance.api_key = "test_api_key"
    binance.api_secret = "test_api_secret"

    # Sample order parameters
    base_currency = 'BTC'
    quote_currency = 'USDC'
    symbol = base_currency + quote_currency
    side = 'SELL'
    order_type = 'MARKET'
    quote_order_qty = round(12 / 98000, 5)

    # Mock response from Binance API

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = constants.binance_successful_sell_market_order_mock_response
    mock_post.return_value = mock_response

    # Call the new_order function for a `MAKER` type order
    response = binance.new_order(base_currency=base_currency,
                                 quote_currency=quote_currency,
                                 side=side,
                                 order_type=order_type,
                                 quantity=quote_order_qty)

    # Test if the response contains the expected values
    assert response["symbol"] == symbol
    assert response["side"] == side
    assert response["type"] == order_type
    assert response["origQty"] == f"{quote_order_qty}000"
    assert response["status"] == "FILLED"

    # Ensure the API was called correctly
    mock_post.assert_called_once()


@patch("requests.post")
def test_new_order_fail(mock_post):
    # Setup the Binance instance or class
    binance = BinanceProxy()
    binance.api_key, binance.api_secret = 'test_api_key', 'test_api_secret'

    # Simulate an error response from Binance (e.g., invalid API key or other issues)
    mock_error_response = {"code": -1003, "msg": "Invalid API Key"}

    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = mock_error_response
    mock_post.return_value = mock_response

    # Call the new_order function
    response = binance.new_order(
        base_currency='BTC',
        quote_currency='USDT',
        side='SELL',
        order_type='LIMIT',
        price=95000,
        quantity=5,
        time_in_force='GTC'
    )

    # Assert that the error message is as expected
    assert response["msg"] == "Invalid API Key"
    assert response["code"] == -1003

    # Ensure the API call was made
    mock_post.assert_called_once()


@patch('requests.delete')
def test_cancel_order(mock_delete):
    # Setup the Binance instance or class
    binance = BinanceProxy()
    binance.api_key, binance.api_secret = 'test_api_key', 'test_api_secret'

    # Simulate a response from Binance
    mock_cancel_response = {
      "symbol": "BTCUSDT",
      "origClientOrderId": "m5CDTq8KTqOcDamZ2Dz6Sz",
      "orderId": 1,
      "orderListId": -1,
      "clientOrderId": "7oyeHZhHmwxYWAIS2Klxoa",
      "transactTime": 1732999865211,
      "price": "90000.00000000",
      "origQty": "0.00011000",
      "executedQty": "0.00000000",
      "cummulativeQuoteQty": "0.00000000",
      "status": "CANCELED",
      "timeInForce": "GTC",
      "type": "LIMIT",
      "side": "BUY",
      "selfTradePreventionMode": "EXPIRE_MAKER"
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_cancel_response
    mock_delete.return_value = mock_response

    response = binance.cancel_order(base_currency='BTC', quote_currency='USDT', order_id=1)

    assert response['status'] == 'CANCELED'
    assert response['orderId'] == 1
    assert response['symbol'] == 'BTCUSDT'

    # Ensure the API call was made
    mock_delete.assert_called_once()