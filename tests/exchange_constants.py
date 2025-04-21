from typing import Dict, List
import json


buda_order_book_response = {
                    "order_book": {
                        "asks": [
                            ["837753.25", "1.40724154"],  # lowest ask
                            ["837597.23", "0.13177617"]
                        ],
                        "bids": [
                            ["836677.14", "0.447349"],    # highest bid
                            ["837462.23", "1.43804963"]
                        ]
                    }
                }

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


successful_batch_order_mock_partial_success_response = {"orders_diff": [
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

successful_batch_order_states_pending = {
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

successful_batch_order_states_sub_orders_traded = {
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

partial_successful_batch_order_mock_response_pending = {
            "orders_diff": [
                {
                    "mode": "place",
                    "order": {
                        "order": {
                            "id": None,
                            "state": "pending",
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
                            "state": "pending",
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

binance_successful_sell_market_order_response_after_cancelaion_profit = {
  "symbol": "ETHUSDC",
  "orderId": 3713981899,
  "orderListId": -1,
  "clientOrderId": "JvCHh6jhpSYzm24YfSU86a",
  "transactTime": 1736099553299,
  "price": "0.00000000",
  "origQty": "0.30000000",
  "executedQty": "0.30000000",
  "origQuoteOrderQty": "0.00000000",
  "cummulativeQuoteQty": "3300.00000000",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "MARKET",
  "side": "SELL",
  "workingTime": 1736099553299,
  "fills": [
    {
      "price": "11000.00000000",
      "qty": "0.30000000",
      "commission": "0.01114035",
      "commissionAsset": "USDC",
      "tradeId": 126826282
    }
  ],
  "selfTradePreventionMode": "EXPIRE_MAKER"
}

binance_ln_invoice_001 = {
  "coin": "BTC",
  "address": "lnbc10m1pncjjq2pp5xr8w2ze0es7atjwkzaqzxtc9plx7dgywu9kppynys49c6dewx80qdqqcqzysxqrrsssp5sgj026j0znjd5a92zadhf73qmyl6synu6ch8zjuxznuqmqyymfqq9qxpqysgqres705w8el7g2s6u5629hylc9g00p822kyflsh7jm5cfn745qkz894djv59psejw4w5rf4jq5pgy74cfudtnq2e9aj37gmeullam6vspr43m7j",
  "url": "https://lightningdecoder.com/lnbc10m1pncjjq2pp5xr8w2ze0es7atjwkzaqzxtc9plx7dgywu9kppynys49c6dewx80qdqqcqzysxqrrsssp5sgj026j0znjd5a92zadhf73qmyl6synu6ch8zjuxznuqmqyymfqq9qxpqysgqres705w8el7g2s6u5629hylc9g00p822kyflsh7jm5cfn745qkz894djv59psejw4w5rf4jq5pgy74cfudtnq2e9aj37gmeullam6vspr43m7j",
  "isDefault": 0
}

buda_ln_invoice_001 = {
    "invoice":
    {
      "id": "Bjkb",
      "encoded_payment_request": "lnbc10m1pncjj6ypp54alcwxtfxam2wev98qcxxmz7mjptxjuckeg6h9v6rvfvtrewf5ssdqqcqzzsxqyz5vqsp57xw865jh9dc0kq4z55zkyfacgw9azfazfh5x8al7j8cc3t9dhmrq9qxpqysgq9svt4fh2w4fl4442dkmghsj8gknqdxq5pteaphdjmpm2gl9lxy3p52ecvuw2la3ndwmpzwvqywdxsfxy2884u5lm6n7x68x7lh6jm0spk3e9hg",
      "currency": "BTC",
      "memo": "null",
      "amount": 1000000,
      "expiration_time": 1737137348,
      "state": "awaiting_payment",
      "price": "null"
    }
}

binance_standardized_ln_invoice_00995 = {
    'coin': 'BTC',
    'invoice': 'lnbc9950u1pncjk4zpp5ynumada7kt9j484ad08uxdgauttqmcjuu6hpeh7p4srjck06uyfqdqqcqzysxqrrsssp54z0z8222dkfkvgx8d4prhg9twphm3njs9u75v2ztmzexwdrvkpcq9qxpqysgqzrfcx8xwkn2and0xpj2zs9hmqfnz3cchhngyl7nyx33upjq93glrcmzew7rcjhxjrgmnlmd5qas0shf760ahedgfcn92twpz77sgsjqqp5z438',
    'amount': 0.00995
}

binance_standardized_ln_invoice_0075 = {
    'coin': 'BTC',
    'invoice': 'lnbc7050u1pncjkh8pp5rq9rp7676z8dc0jvg0hfd7xvns3hrqkakcm0zu2rgg06r8eku0qqdqqcqzysxqrrsssp5d6myfjn9sq8w0u9f29tvuga856v3x4cn5ax6yn8uer4zteqjq2ss9qxpqysgqyf7g6fqkep6f7zjxuvl9avt2geerl9p06hrcqycrdj8nwdnpy7zhqveznpn9vvssqaa8mcagw7sxuk4ww0cfvjtp8sa2ym84l0g7vpsqfexnu4',
    'amount': 0.00705
}

binance_withdrawal_history: List[Dict] = [
    {
        'id': '156e566fe1d04820a4b6b46d53a96570',
        'amount': '0.00005',
        'transactionFee': '0.000001',
        'coin': 'BTC',
        'status': 6,
        'address': 'lnbc50u1pn5f8ljpp5dc6y936p79j9dfqs59vdkz6dfurxcgzvsren4mtahdrva9paqxhsdq8w3jhxaqcqzzsxqyz5vqsp5yp9j2fghxfw4dvxnkcu5lyldykew7ymuq27f8jpay8ms7q9kwe9s9qxpqysgqqczpcedj6ry8t8z5emqvz9mvjr263fsv7p64st6j5pyxfcdmm9hparffkgfsxv883kh6hkczfgpktlevn3rldcskqv392fk8n7ad3lcp6yx88t', 'txId': '6e3442c741f16456a410a158db0b4d4f066c204c80f33aed7dbb46ce943d01af',
        'applyTime': '2024-11-25 16:12:15',
        'network': 'LIGHTNING',
        'transferType': 0,
        'info': 'broadcast:03a1f3afd646d77bdaf545cceaf079bab6057eae52c6319b63b5803d0989d6a72f',
        'confirmNo': 1,
        'walletType': 0,
        'txKey': '',
        'completeTime': '2024-11-25 16:13:43',
        'state': 'confirmed'
     }
]

binance_withdrawal_history_USDC: List[Dict] = [
    {
        'id': '7b32ca91132c45ca929ded6cdcf8ac74',
        'amount': '11.5', 'transactionFee': '8.5',
        'coin': 'USDC',
        'status': 6,
        'address': '0x4f56c765e4a5ae10d924235a2c813e8b260a3291',
        'txId': '0xa3599321fec630a2a6bc88170f2c5e7adc9ef006c34962ee50250a50cda02590',
        'applyTime': '2025-01-20 18:15:17',
        'network': 'ETH',
        'transferType': 0,
        'info': '0x28c6c06298d514db089934071355e5743bf21d60,11482483',
        'confirmNo': 48, 'walletType': 0,
        'txKey': '',
        'completeTime': '2025-01-20 18:17:41',
        'state': 'confirmed'}
]

binance_deposit_history: List[Dict] = [
    {
        'id': '4275309289780248321',
        'amount': '0.00002',
        'coin': 'BTC',
        'network': 'LIGHTNING',
        'status': 1,
        'address': 'f4587ae111ad5e240825c45c243cd94e940fd5c6411ca0e415fd829c7c01f151',
        'addressTag': '',
        'sourceAddress': 'anonymous',
        'txId': 'f4587ae111ad5e240825c45c243cd94e940fd5c6411ca0e415fd829c7c01f151',
        'insertTime': 1732786692000,
        'transferType': 0,
        'confirmTimes': '1/1',
        'unlockConfirm': 0,
        'walletType': 0,
        'state': 'confirmed'
    },
    {
        'id': '4274477811878035201',
        'amount': '0.00002',
        'coin': 'BTC',
        'network': 'LIGHTNING',
        'status': 1,
        'address': '7694ad578f85974b52281b1b11cef9c2760e075fff84980fff10c9da0fe8079d',
        'addressTag': '',
        'sourceAddress': 'anonymous',
        'txId': '7694ad578f85974b52281b1b11cef9c2760e075fff84980fff10c9da0fe8079d',
        'insertTime': 1732737132000,
        'transferType': 0,
        'confirmTimes': '1/1',
        'unlockConfirm': 0,
        'walletType': 0,
        'state': 'confirmed'
    },
    {
        'id': '4268630286331928321',
        'amount': '0.00002',
        'coin': 'BTC',
        'network': 'LIGHTNING',
        'status': 1,
        'address': 'dd93e6c4b129bbec44a315a87655b04f836556c396986307341ef00b03a41ce5',
        'addressTag': '',
        'sourceAddress': 'anonymous',
        'txId': 'dd93e6c4b129bbec44a315a87655b04f836556c396986307341ef00b03a41ce5',
        'insertTime': 1732388592000,
        'transferType': 0,
        'confirmTimes': '1/1',
        'unlockConfirm': 0,
        'walletType': 0,
        'state': 'confirmed'
    }
]

buda_withdrawal_history: List[Dict] = [
    {
        'id': 'EwjxVM',
        'uuid': '61da848a-a0f8-4657-b045-09653bb7a9d8',
        'state': 'rejected',
        'currency': 'BTC',
        'created_at': '2024-11-28T09:38:05.305Z',
        'withdrawal_data':
            {
                'type': 'lightning_network_withdrawal_data',
                'payment_request': 'lnbc20u1pn5swdvpp573v84cg3440zgzp9c3wzg0xef62ql4wxgyw2peq4lkpfclqp79gsdqqcqzysxqrrsssp58736wslm5tw8r9eep0fmysj60mf705e5dkk24nxyhpvnp5naaasq9qxpqysgqdfrr8ry3lvrpekepjj9dxualwea305v2craa5c8qy6ww9809tyeksg8s7tue5h3g48xdldc8y3hlfcvx952dk44wl60uprznqx4ehnqpaxjxfv',
                'payment_error': 'Invoice already paid',
                'total_fees': None
            },
        'forced_reason': None,
        'account_id': 143870,
        'user_id': 143870,
        'expected_execution_time': None,
        'expected_arrival_time': None,
        'hold_execution': False,
        'reserve_name': 'LN BTC',
        'reserve_code': 'ln-btc',
        'rejection_reasons': [],
        'amount': ['0.00002', 'BTC'],
        'fee': ['0.0', 'BTC'],
        'usd_amount': ['1.89', 'USD']
    },
    {
        'id': 'WBbWyN',
        'uuid': '294df727-33c8-489e-abdc-69f728985afc',
        'state': 'confirmed',
        'currency': 'BTC',
        'created_at': '2024-11-28T09:37:47.101Z',
        'withdrawal_data':
            {
                'type': 'lightning_network_withdrawal_data',
                'payment_request': 'lnbc20u1pn5swdvpp573v84cg3440zgzp9c3wzg0xef62ql4wxgyw2peq4lkpfclqp79gsdqqcqzysxqrrsssp58736wslm5tw8r9eep0fmysj60mf705e5dkk24nxyhpvnp5naaasq9qxpqysgqdfrr8ry3lvrpekepjj9dxualwea305v2craa5c8qy6ww9809tyeksg8s7tue5h3g48xdldc8y3hlfcvx952dk44wl60uprznqx4ehnqpaxjxfv',
                'payment_error': None,
                'total_fees': ['0.0', 'BTC']
            },
        'forced_reason': None,
        'account_id': 143870,
        'user_id': 143870,
        'expected_execution_time': None,
        'expected_arrival_time': None,
        'hold_execution': False,
        'reserve_name': 'LN BTC',
        'reserve_code': 'ln-btc',
        'rejection_reasons': [],
        'amount': ['0.00002', 'BTC'],
        'fee': ['0.0', 'BTC'],
        'usd_amount': ['1.89', 'USD']
    },
    {
        'id': 'VWBwmE',
        'uuid': '9803d6c9-2aa1-459e-8b27-bec08c35709a',
        'state': 'confirmed'
    }
]

buda_deposit_history: List[Dict] = [
    {
        'id': 'lNxKKG',
        'state': 'confirmed',
        'currency': 'BTC',
        'created_at': '2024-11-27T19:56:55.735Z',
        'deposit_data': {
            'type': 'lightning_network/deposit_data',
            'invoice': {
                'id': 'oEAd',
                'encoded_payment_request': 'lnbc50u1pn5w7f3pp5xsakzk4vfwa88xwdjgfts39jse42v7enu0xhxdev7fwnppkdavfqdq8w3jhxaqcqzzsxqyz5vqsp55se2cdn829gd5xrt6rx54xz2umsfcfygeg9rtl8a0g73jk0m90vq9qxpqysgqumy7k7dddfjzv3xkt493w0fzxa7mds3kqvfna0laamk3fcxrpldrjlf9z39thhqj5848tkvyznvj7e8fer4mhgtrcdh7wu86hrue85spaeqs9x',
                'currency': 'BTC',
                'memo': 'test',
                'amount': 5000,
                'expiration_time': 1732823729,
                'state': 'settled',
                'price': None
            }
        },
        'account_id': 143870,
        'user_id': 143870,
        'order_id': None,
        'order_type': None,
        'state_reason': None,
        'expected_arrival_time': None,
        'reserve_name': 'LN BTC',
        'reserve_code': 'ln-btc',
        'amount': ['0.00005', 'BTC'],
        'fee': ['0.0', 'BTC']}
    ]

buda_withdrawal_response = {
            'id': 'VWBwmE',
            'uuid': '9803d6c9-2aa1-459e-8b27-bec08c35709a',
            'state': 'executing',
            'currency': 'BTC',
            'created_at': '2025-01-19T14:50:24.065Z',
            'withdrawal_data':
                {
                    'type': 'lightning_network_withdrawal_data',
                    'payment_request': 'lnbc100u1pnc6y8ypp5e072s204a899se3z4fky8z58sqlanejhmjadq4e564h4uxglg0eqdqqcqzysxqrrsssp52vhc2uuzgarshmw962fnnq2veash9rj7vcqyj5zjvqlv05fdzxss9qxpqysgq0fx5ajd5m5jy9jy6pjacmcsw3xlatpdqzt3chmm82t8v0ffphg7jfy59lm73twwc00w89msy5wgrkqzaffjvq4gkpw8qd0k5qw7kj8qqr8p6r6',
                    'payment_error': None,
                    'total_fees': None
                },
            'forced_reason': None,
            'account_id': 143870,
            'user_id': 143870,
            'expected_execution_time': None,
            'expected_arrival_time': None,
            'hold_execution': False,
            'reserve_name': 'LN BTC',
            'reserve_code': 'ln-btc',
            'rejection_reasons': [],
            'amount': ['0.0001', 'BTC'],
            'fee': ['0.0', 'BTC'],
            'usd_amount': ['10.46', 'USD']
        }

binance_withdrawal_response = {
    "id": "156e566fe1d04820a4b6b46d53a96570"
}

binance_withdrawal_usdc_response = {
    'id': '7b32ca91132c45ca929ded6cdcf8ac74'
}

buda_withdrawal_usdc_response: Dict = {
    'id': 'bgRpYj',
    'uuid': '31f9dccc-fc0a-41d7-80a1-47e634b91825',
    'state': 'executing',
    'currency': 'USDC',
    'created_at': '2025-01-20T18:35:59.725Z',
    'withdrawal_data': {
        'type': 'usdc_withdrawal_data',
        'target_address': '0xc49cc35273f59ba0abec3bf6d895ba15d3a6027b',
        'direct': False,
        'tx_hash': None,
        'direct_hash': None,
        'carbon_footprint_donation_confirmed': False,
        'carbon_footprint_donation': None
    },
    'forced_reason': None,
    'account_id': 143870,
    'user_id': 143870,
    'expected_execution_time': None,
    'expected_arrival_time': None,
    'hold_execution': False,
    'reserve_name': 'USDC',
    'reserve_code': 'usdc',
    'rejection_reasons': [],
    'amount': ['20.0', 'USDC'],
    'fee': ['6.0', 'USDC'],
    'usd_amount': ['19.84', 'USD']
}

binance_usdc_address_ERC20_response = {
    "coin": "USDC",
    "address": "0xc49cc35273f59ba0abec3bf6d895ba15d3a6027b",
    "tag": "",
    "url": "https://etherscan.io/address/0xc49cc35273f59ba0abec3bf6d895ba15d3a6027b",
    "isDefault": 0
}

buda_usdc_address_ERC20_response = {
    "receive_address":
        {
            "id": 270780,
            "address": "0x4f56c765e4a5ae10d924235a2c813e8b260a3291",
            "created_at": "2025-01-20T11:45:39.000Z",
            "used": False,
            "ready": True}
}

buda_usdc_withdrawal_history: List[Dict] = [
    {
        'id': 'DdBYRG',
        'uuid': '34b8bfa0-5211-4028-8398-db8f5a76e9d9',
        'state': 'confirmed',
        'currency': 'USDC',
        'created_at': '2025-01-23T14:39:30.715Z',
        'withdrawal_data':
            {
                'type': 'usdc_withdrawal_data',
                'target_address': '0xc49cc35273f59ba0abec3bf6d895ba15d3a6027b',
                'direct': False,
                'tx_hash': '0x3d9dcca2887020a93438ceef165fb27ca0576a5fcf6467c4ac18cf50a15a5e8d',
                'direct_hash': None,
                'carbon_footprint_donation_confirmed': False,
                'carbon_footprint_donation': None
            },
        'forced_reason': None,
        'account_id': 143870,
        'user_id': 143870,
        'expected_execution_time': None,
        'expected_arrival_time': None,
        'hold_execution': False,
        'reserve_name': 'USDC',
        'reserve_code': 'usdc',
        'rejection_reasons': [],
        'amount': ['20.0', 'USDC'],
        'fee': ['8.0', 'USDC'],
        'usd_amount': ['20.1', 'USD']
    },
    {
        'id': 'dMbExR',
        'uuid': '892acaad-0e05-4649-9f3d-f1ce37a9b083',
        'state': 'confirmed',
        'currency': 'USDC',
        'created_at': '2025-01-23T14:35:38.941Z',
        'withdrawal_data':
            {
                'type': 'usdc_withdrawal_data',
                'target_address': '0xc49cc35273f59ba0abec3bf6d895ba15d3a6027b',
                'direct': False,
                'tx_hash': '0x3d9dcca2887020a93438ceef165fb27ca0576a5fcf6467c4ac18cf50a15a5e8d',
                'direct_hash': None,
                'carbon_footprint_donation_confirmed': False,
                'carbon_footprint_donation': None
            },
        'forced_reason': None,
        'account_id': 143870,
        'user_id': 143870,
        'expected_execution_time': None,
        'expected_arrival_time': None,
        'hold_execution': False,
        'reserve_name': 'USDC',
        'reserve_code': 'usdc',
        'rejection_reasons': [],
        'amount': ['20.0', 'USDC'],
        'fee': ['6.0', 'USDC'],
        'usd_amount': ['20.1', 'USD']
    },
    {
        'id': 'bgRpYj',
        'uuid': '31f9dccc-fc0a-41d7-80a1-47e634b91825',
        'state': 'confirmed',
        'currency': 'USDC',
        'created_at': '2025-01-20T18:35:59.725Z',
        'withdrawal_data':
            {
                'type': 'usdc_withdrawal_data',
                'target_address': '0xc49cc35273f59ba0abec3bf6d895ba15d3a6027b',
                'direct': False,
                'tx_hash': '0x119eaf9e4944d77ebf2df324bf1af3f0c597d5869fb302d223ec9e513f2739bb',
                'direct_hash': None,
                'carbon_footprint_donation_confirmed': False,
                'carbon_footprint_donation': None
            },
        'forced_reason': None,
        'account_id': 143870,
        'user_id': 143870,
        'expected_execution_time': None,
        'expected_arrival_time': None,
        'hold_execution': False,
        'reserve_name': 'USDC',
        'reserve_code': 'usdc',
        'rejection_reasons': [],
        'amount': ['20.0', 'USDC'],
        'fee': ['6.0', 'USDC'],
        'usd_amount': ['19.84', 'USD']
    }
]

binance_get_price_response: Dict[str, str] = {
    'symbol': 'BTCUSDC',
    'price': '104738.01000000'
}

buda_get_price_response: Dict[str, str] = {
    'symbol': 'BTCUSDC',
    'price': '103507.07'
}