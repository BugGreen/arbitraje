successful_batch_order = [
            {
                "mode": "place",
                "order": {
                    "amount": 0.0012,
                    "limit": 15000000,
                    "market_name": "eth-cop",
                    "price_type": "limit",
                    "type": "Bid"
                }
            },
            {
                "mode": "place",
                "order": {
                    "amount": 0.0012,
                    "limit": 15000000,
                    "market_name": "eth-cop",
                    "price_type": "limit",
                    "type": "Bid"
                }
            }
        ]

expected_successful_batch_order_response = [
            {
                "id": 1306565374,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.001000001",
                    "ETH"
                ],
                "traded_amount": [
                    "0.0",
                    "ETH"
                ],
                "total_exchanged": [
                    "0.0",
                    "COP"
                ]
            },
            {
                "id": 1306565375,
                "status": "received",
                "error_message": "null",
                "amount": [
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
                ]
            }
        ]

successful_batch_order_mock_response = {"orders_diff": [
                {
                  "mode": "place",
                  "order": {
                    "order": {
                      "id": 1306565374,
                      "uuid": "fb9bc6ff-d73a-483d-b185-4292f4d3adf8",
                      "market_id": "ETH-COP",
                      "account_id": 143870,
                      "type": "Bid",
                      "state": "received",
                      "created_at": "2024-12-27T14:04:32.810Z",
                      "fee_currency": "ETH",
                      "price_type": "limit",
                      "source": "null",
                      "client_id": "null",
                      "message": "null",
                      "order_type": "gtc",
                      "expire_at": 0,
                      "limit": [
                        "10000000.0",
                        "COP"
                      ],
                      "amount": [
                        "0.001000001",
                        "ETH"
                      ],
                      "original_amount": [
                        "0.001000001",
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
                    }
                  }
                },
                {
                  "mode": "place",
                  "order": {
                    "order": {
                      "id": 1306565375,
                      "uuid": "37bf5d0f-548a-40d1-9893-6a8e078bfb94",
                      "market_id": "ETH-COP",
                      "account_id": 143870,
                      "type": "Bid",
                      "state": "received",
                      "created_at": "2024-12-27T14:04:32.830Z",
                      "fee_currency": "ETH",
                      "price_type": "limit",
                      "source": "null",
                      "client_id": "null",
                      "message": "null",
                      "order_type": "gtc",
                      "expire_at": 0,
                      "limit": [
                        "10000000.0",
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
                    }
                  }
                }
              ]}

successful_batch_order_states = {
  "orders": [
    {
      "id": 1306565374,
      "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
      "market_id": "ETH-COP",
      "account_id": 143870,
      "type": "Bid",
      "state": "pending",
      "created_at": "2024-12-27T19:01:35.154Z",
      "fee_currency": "ETH",
      "price_type": "limit",
      "source": "null",
      "client_id": "null",
      "message": "null",
      "order_type": "gtc",
      "expire_at": 0,
      "limit": [
        "10000000.0",
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
        "12000.0",
        "COP"
      ],
      "paid_fee": [
        "0.0",
        "ETH"
      ],
      "stop_price": "null"
    },
    {
          "id": 1306565375,
          "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
          "market_id": "ETH-COP",
          "account_id": 143870,
          "type": "Bid",
          "state": "pending",
          "created_at": "2024-12-27T19:01:35.154Z",
          "fee_currency": "ETH",
          "price_type": "limit",
          "source": "null",
          "client_id": "null",
          "message": "null",
          "order_type": "gtc",
          "expire_at": 0,
          "limit": [
              "10000000.0",
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
      }
  ]
}

partial_successful_batch_order = [
            {
                "mode": "place",
                "order": {
                    "amount": 1.001000001,  # Intentional large amount to trigger 'unprepared'
                    "limit": 10000000.0,
                    "market_name": "eth-cop",
                    "price_type": "limit",
                    "type": "Bid"
                }
            },
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

expected_partial_successful_batch_order_response = [
            {
                "id": None,
                "status": "unprepared",
                "error_message": "insolvent",
                "amount": [
                    "1.001000001",
                    "ETH"
                ],
                "traded_amount": [
                    "0.0",
                    "ETH"
                ],
                "total_exchanged": [
                    "0.0",
                    "COP"
                ]
            },
            {
                "id": 1306566197,
                "status": "received",
                "error_message": None,
                "amount": None
            }
        ]

partial_successful_batch_order_mock_response = {
            "orders_diff": [
                {
                    "mode": "place",
                    "order": {
                        "order": {
                            "id": None,
                            "state": "unprepared",
                            "message": "insolvent",
                            "amount": [
                                "1.001000001",
                                "ETH"
                            ]
                        }
                    }
                },
                {
                    "mode": "place",
                    "order": {
                        "order": {
                            "id": 1306566197,
                            "state": "received",
                            "message": None
                        }
                    }
                }
            ]
        }

amount_less_than_minimum_order = [
            {
                "mode": "place",
                "order": {
                    "amount": 0.0005,  # Below minimum
                    "limit": 10000000.0,
                    "market_name": "eth-cop",
                    "price_type": "limit",
                    "type": "Bid"
                }
            }
        ]

expected_amount_less_than_minimum_response = {
            "error_code": "EXCHANGE_API_ERROR_invalid_record",
            "message": "Validation Failed",
            "details": [
                {
                  "resource": "Bid",
                  "field": "amount_cents",
                  "code": "amount_less_than_minimum",
                  "message": "Amount less than minimum"
                }
              ]
            }

amount_less_than_minimum_order_mock_response = {
            "message": "Validation Failed",
            "code": "invalid_record",
            "errors": [
                {
                    "resource": "Bid",
                    "field": "amount_cents",
                    "code": "amount_less_than_minimum",
                    "message": "Amount less than minimum"
                }
            ]
        }

sub_orders_to_cancel_states = {
  "orders": [
    {
      "id": 130000,
      "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
      "market_id": "ETH-COP",
      "account_id": 143870,
      "type": "Bid",
      "state": "canceled_and_traded",
      "created_at": "2024-12-27T19:01:35.154Z",
      "fee_currency": "ETH",
      "price_type": "limit",
      "source": "null",
      "client_id": "null",
      "message": "null",
      "order_type": "gtc",
      "expire_at": 0,
      "limit": [
        "10000.0",
        "COP"
      ],
      "amount": [
        "0.3",
        "ETH"
      ],
      "original_amount": [
        "0.3",
        "ETH"
      ],
      "traded_amount": [
        "0.3",
        "ETH"
      ],
      "total_exchanged": [
        "3000.0",
        "COP"
      ],
      "paid_fee": [
        "0.0",
        "ETH"
      ],
      "stop_price": "null"
    },
    {
          "id": 130001,
          "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
          "market_id": "ETH-COP",
          "account_id": 143870,
          "type": "Bid",
          "state": "canceled",
          "created_at": "2024-12-27T19:01:35.154Z",
          "fee_currency": "ETH",
          "price_type": "limit",
          "source": "null",
          "client_id": "null",
          "message": "null",
          "order_type": "gtc",
          "expire_at": 0,
          "limit": [
              "10000.0",
              "COP"
          ],
          "amount": [
              "0.7",
              "ETH"
          ],
          "original_amount": [
              "0.7",
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
      }
  ]
}

sub_orders_canceled_response = {
  "orders_diff": [
    {
      "mode": "cancel",
      "order_id": 130000
    },
    {
      "mode": "cancel",
      "order_id": 130001
    }
  ]
}

binance_successful_market_order_mock_response = {
  "symbol": "BTCUSDC",
  "orderId": 3713777788,
  "orderListId": -1,
  "clientOrderId": "7yeLO2VOqxEVS8C9a2so29",
  "transactTime": 1736094661640,
  "price": "0.00000000",
  "origQty": "0.00009000",
  "executedQty": "0.00009000",
  "origQuoteOrderQty": "9.00000000",
  "cummulativeQuoteQty": "8.81927910",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "BUY",
  "workingTime": 1736094661640,
  "fills": [
    {
      "price": "97991.99000000",
      "qty": "0.00009000",
      "commission": "0.00000936",
      "commissionAsset": "BNB",
      "tradeId": 126821747
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

binance_successful_sell_market_order_mock_response = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.00012000",
  "executedQty": "0.00012000",
  "origQuoteOrderQty": "0.00000000",
  "cummulativeQuoteQty": "11.72668560",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "97722.38000000",
      "qty": "0.00012000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

batch_order_response_to_excecute_in_binance = [
            {
                "id": 1306565374,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.200000000",
                    "BTC"
                ],
                "traded_amount": [
                    "0.0",
                    "ETH"
                ],
                "total_exchanged": [
                    "0.0",
                    "USDC"
                ]
            },
            {
                "id": 1306565375,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.8",
                    "BTC"
                ],
                "traded_amount": [
                    "0.0",
                    "BTC"
                ],
                "total_exchanged": [
                    "0.0",
                    "USDC"
                ]
            }
        ]

sub_orders_to_execute_in_binance_states = {
  "orders": [
    {
      "id": 130000,
      "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
      "market_id": "BTC-USDC",
      "account_id": 143870,
      "type": "Bid",
      "state": "traded",
      "created_at": "2024-12-27T19:01:35.154Z",
      "fee_currency": "BTC",
      "price_type": "limit",
      "source": "null",
      "client_id": "null",
      "message": "null",
      "order_type": "gtc",
      "expire_at": 0,
      "limit": [
        "1000.0",
        "USDC"
      ],
      "amount": [
        "0.2",
        "BTC"
      ],
      "original_amount": [
        "0.2",
        "BTC"
      ],
      "traded_amount": [
        "0.2",
        "BTC"
      ],
      "total_exchanged": [
        "200.0",
        "USDC"
      ],
      "paid_fee": [
        "0.0",
        "BTC"
      ],
      "stop_price": "null"
    },
    {
          "id": 130001,
          "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
          "market_id": "BTC-USDC",
          "account_id": 143870,
          "type": "Bid",
          "state": "pending",
          "created_at": "2024-12-27T19:01:35.154Z",
          "fee_currency": "BTC",
          "price_type": "limit",
          "source": "null",
          "client_id": "null",
          "message": "null",
          "order_type": "gtc",
          "expire_at": 0,
          "limit": [
              "1000.0",
              "USDC"
          ],
          "amount": [
              "0.8",
              "BTC"
          ],
          "original_amount": [
              "0.8",
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
              "0.0",
              "BTC"
          ],
          "stop_price": "null"
      }
  ]
}

binance_successful_sell_market_order_response = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.20000000",
  "executedQty": "0.20000000",
  "origQuoteOrderQty": "0.00000000",
  "cummulativeQuoteQty": "200.00000000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "1100.00000000",
      "qty": "0.20000000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

binance_successful_sell_market_order_response_base = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.18181000",
  "executedQty": "0.18181000",
  "origQuoteOrderQty": "200.00000000",
  "cummulativeQuoteQty": "199.99000000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "1100.00000000",
      "qty": "0.18181000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

binance_successful_sell_market_order_response_base_no_profit = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.22222000",
  "executedQty": "0.22222000",
  "origQuoteOrderQty": "200.00000000",
  "cummulativeQuoteQty": "199.99800000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "900.00000000",
      "qty": "0.22222000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

binance_successful_sell_market_order_response_quote_no_profit = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.20000000",
  "executedQty": "0.20000000",
  "origQuoteOrderQty": "0.00000000",
  "cummulativeQuoteQty": "180.00000000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "900.00000000",
      "qty": "0.20000000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}


binance_successful_sell_market_order_response_quotes_profit = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.50000000",
  "executedQty": "0.50000000",
  "origQuoteOrderQty": "0.00000000",
  "cummulativeQuoteQty": "500.00000000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "1100.00000000",
      "qty": "0.50000000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

sub_orders_to_execute_in_binance_multiple_traded_states = {
  "orders": [
    {
      "id": 130000,
      "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
      "market_id": "BTC-USDC",
      "account_id": 143870,
      "type": "Bid",
      "state": "traded",
      "created_at": "2024-12-27T19:01:35.154Z",
      "fee_currency": "BTC",
      "price_type": "limit",
      "source": "null",
      "client_id": "null",
      "message": "null",
      "order_type": "gtc",
      "expire_at": 0,
      "limit": [
        "1000.0",
        "USDC"
      ],
      "amount": [
        "0.5",
        "BTC"
      ],
      "original_amount": [
        "0.5",
        "BTC"
      ],
      "traded_amount": [
        "0.5",
        "BTC"
      ],
      "total_exchanged": [
        "500.0",
        "USDC"
      ],
      "paid_fee": [
        "0.0",
        "BTC"
      ],
      "stop_price": "null"
    },
    {
          "id": 130001,
          "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
          "market_id": "BTC-USDC",
          "account_id": 143870,
          "type": "Bid",
          "state": "traded",
          "created_at": "2024-12-27T19:01:35.154Z",
          "fee_currency": "BTC",
          "price_type": "limit",
          "source": "null",
          "client_id": "null",
          "message": "null",
          "order_type": "gtc",
          "expire_at": 0,
          "limit": [
              "1000.0",
              "USDC"
          ],
          "amount": [
              "0.5",
              "BTC"
          ],
          "original_amount": [
              "0.5",
              "BTC"
          ],
          "traded_amount": [
              "0.5",
              "BTC"
          ],
          "total_exchanged": [
              "500.0",
              "USDC"
          ],
          "paid_fee": [
              "0.0",
              "BTC"
          ],
          "stop_price": "null"
      }
  ]
}


sub_orders_to_execute_in_binance_states_with_one_less_than_minimum = {
  "orders": [
    {
      "id": 130000,
      "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
      "market_id": "BTC-USDC",
      "account_id": 143870,
      "type": "Bid",
      "state": "traded",
      "created_at": "2024-12-27T19:01:35.154Z",
      "fee_currency": "BTC",
      "price_type": "limit",
      "source": "null",
      "client_id": "null",
      "message": "null",
      "order_type": "gtc",
      "expire_at": 0,
      "limit": [
        "1000.0",
        "USDC"
      ],
      "amount": [
        "0.192",
        "BTC"
      ],
      "original_amount": [
        "0.192",
        "BTC"
      ],
      "traded_amount": [
        "0.192",
        "BTC"
      ],
      "total_exchanged": [
        "192.0",
        "USDC"
      ],
      "paid_fee": [
        "0.0",
        "BTC"
      ],
      "stop_price": "null"
    },
    {
          "id": 130001,
          "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
          "market_id": "BTC-USDC",
          "account_id": 143870,
          "type": "Bid",
          "state": "traded",
          "created_at": "2024-12-27T19:01:35.154Z",
          "fee_currency": "BTC",
          "price_type": "limit",
          "source": "null",
          "client_id": "null",
          "message": "null",
          "order_type": "gtc",
          "expire_at": 0,
          "limit": [
              "1000.0",
              "USDC"
          ],
          "amount": [
              "0.008",
              "BTC"
          ],
          "original_amount": [
              "0.008",
              "BTC"
          ],
          "traded_amount": [
              "0.008",
              "BTC"
          ],
          "total_exchanged": [
              "8.0",
              "USDC"
          ],
          "paid_fee": [
              "0.0",
              "BTC"
          ],
          "stop_price": "null"
      },
      {
          "id": 130002,
          "uuid": "ab74839f-231a-4755-b69e-5c3c6033924e",
          "market_id": "BTC-USDC",
          "account_id": 143870,
          "type": "Bid",
          "state": "traded",
          "created_at": "2024-12-27T19:01:35.154Z",
          "fee_currency": "BTC",
          "price_type": "limit",
          "source": "null",
          "client_id": "null",
          "message": "null",
          "order_type": "gtc",
          "expire_at": 0,
          "limit": [
              "1000.0",
              "USDC"
          ],
          "amount": [
              "0.8",
              "BTC"
          ],
          "original_amount": [
              "0.8",
              "BTC"
          ],
          "traded_amount": [
              "0.8",
              "BTC"
          ],
          "total_exchanged": [
              "800.0",
              "USDC"
          ],
          "paid_fee": [
              "0.0",
              "BTC"
          ],
          "stop_price": "null"
      },
  ]
}

binance_successful_sell_market_order_response_with_less_than_minimum_1 = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.19200000",
  "executedQty": "0.19200000",
  "origQuoteOrderQty": "0.00000000",
  "cummulativeQuoteQty": "211.20000000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "1100.00000000",
      "qty": "0.19200000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

binance_successful_sell_market_order_response_with_less_than_minimum_2 = {
  "symbol": "BTCUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.80800000",
  "executedQty": "0.80800000",
  "origQuoteOrderQty": "0.00000000",
  "cummulativeQuoteQty": "888.80000000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "1100.00000000",
      "qty": "0.80800000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

