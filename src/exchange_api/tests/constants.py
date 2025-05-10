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
                "id": "1306565374",
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.001000001",
                    "ETH"
                ]
            },
            {
                "id": "1306565375",
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.0012",
                    "ETH"
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
                ]
            },
            {
                "id": "1306566197",
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