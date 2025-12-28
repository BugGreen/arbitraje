expected_insolvent_error_response = {
    "error_code": "INSUFFICIENT_FUNDS",
    "message": "One or more sub-orders could not be processed (insolvent).",
    "sub_order": {
        'id': None,
        'status': 'unprepared',
        'error_message': 'insolvent',
        'amount': ['1.001000001', 'ETH'],
        'traded_amount': None,
        'total_exchanged': None
    }
    }


expected_amount_less_than_minimum_response = {
    'error_code': 'AMOUNT_LESS_THAN_MINIMUM',
    'message': 'One or more orders had an amount less than the exchange minimum.',
    'details': [
        {
            'resource': 'Bid',
            'field': 'amount_cents',
            'code': 'amount_less_than_minimum',
            'message': 'Amount less than minimum'
         }
    ]
}

placed_sub_orders_to_cancel_response = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.3",
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
                "id": 130001,
                "status": "received",
                "error_message": "null",
                "amount": [
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
                ]
            }
        ]

expected_sub_orders_cancelled_response = [
            {
                "id": 130000,
                "status": "canceled_and_traded",
                "error_message": "null",
                "amount": [
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
                ]
            },
            {
                "id": 130001,
                "status": "canceled",
                "error_message": "null",
                "amount": [
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
                ]
            }
        ]

placed_sub_orders_to_execute_in_binance = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.2",
                    "BTC"
                ],
                "traded_amount": [
                    "5.0",
                    "BTC"
                ],
                "total_exchanged": [
                    "200.0",
                    "USDC"
                ]
            },
            {
                "id": 130001,
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

placed_sub_orders_to_execute_in_binance_quote_profit = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.2",
                    "BTC"
                ],
                "traded_amount": [
                    "5.0",
                    "BTC"
                ],
                "total_exchanged": [
                    "200.0",
                    "USDC"
                ]
            },
            {
                "id": 130001,
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

placed_sub_orders_to_execute_in_binance_buy_limit = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.2",
                    "BTC"
                ],
                "traded_amount": [
                    "5.0",
                    "BTC"
                ],
                "total_exchanged": [
                    "200.0",
                    "USDC"
                ]
            },
            {
                "id": 130001,
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

placed_sub_orders_to_execute_in_binance_quote_no_profit = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.2",
                    "BTC"
                ],
                "traded_amount": [
                    "5.0",
                    "BTC"
                ],
                "total_exchanged": [
                    "200.0",
                    "USDC"
                ]
            },
            {
                "id": 130001,
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

placed_sub_orders_to_execute_in_binance_quote_multiple_profit = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.2",
                    "BTC"
                ],
                "traded_amount": [
                    "5.0",
                    "BTC"
                ],
                "total_exchanged": [
                    "200.0",
                    "USDC"
                ]
            },
            {
                "id": 130001,
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

placed_sub_orders_to_execute_in_binance_base_profit = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
                    "0.2",
                    "BTC"
                ],
                "traded_amount": [
                    "5.0",
                    "BTC"
                ],
                "total_exchanged": [
                    "200.0",
                    "USDC"
                ]
            },
            {
                "id": 130001,
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

placed_sub_orders_to_execute_in_binance_multiple_profit = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
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
                ]
            },
            {
                "id": 130001,
                "status": "traded",
                "error_message": "null",
                "amount": [
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
                ]
            }
        ]

placed_sub_orders_to_execute_in_binance_with_one_less_than_minimum = [
            {
                "id": 130000,
                "status": "received",
                "error_message": "null",
                "amount": [
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
                ]
            },
            {
                "id": 130001,
                "status": "received",
                "error_message": "null",
                "amount": [
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
                ]
            },
            {
                "id": 130002,
                "status": "received",
                "error_message": "null",
                "amount": [
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
                ]
            }
        ]

place_sub_orders_sell_limit_flow = [
    {
        'id': 1366131842,
        'status': 'pending',
        'error_message': None,
        'amount': ['0.00066094', 'BTC'],
        'traded_amount': ['0.0', 'BTC'],
        'total_exchanged': ['0.0', 'USDC']
    },
    {
        'id': 1366131843,
        'status': 'pending',
        'error_message': None,
        'amount': ['0.00028306', 'BTC'],
        'traded_amount': ['0.0', 'BTC'],
        'total_exchanged': ['0.0', 'USDC']
    }
]

batch_cancellation_sell_limit_flow = {
    'orders_diff': [{'mode': 'cancel', 'order_id': 1366137957},
                    {'mode': 'cancel', 'order_id': 1366137959}]
}

new_order_binance_sell_limit_flow = {
    'symbol': 'BTCUSDC',
    'orderId': 3956645155,
    'orderListId': -1,
    'clientOrderId': 'w21bG9cLBFlxsex9njFofN',
    'transactTime': 1738257610589,
    'price': '0.00000000',
    'origQty': '0.00010000',
    'executedQty': '0.00010000',
    'origQuoteOrderQty': '0.00000000',
    'cummulativeQuoteQty': '10.53887700',
    'status': 'FILLED',
    'timeInForce': 'GTC',
    'type': 'MARKET',
    'side': 'BUY',
    'workingTime': 1738257610589,
    'fills': [
        {
            'price': '105388.77000000',
            'qty': '0.00010000',
            'commission': '0.00000010',
            'commissionAsset': 'BTC',
            'tradeId': 133136175
        }
    ],
    'selfTradePreventionMode': 'EXPIRE_MAKER'
}