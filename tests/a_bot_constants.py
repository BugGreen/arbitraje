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

place_sub_orders_buy_limit_flow = [
    {
        'id': 1366298103,
        'status': 'pending',
        'error_message': None,
        'amount': ['0.00066572', 'BTC'],
        'traded_amount': ['0.0', 'BTC'],
        'total_exchanged': ['0.0', 'USDC']
    },
    {
        'id': 1366298105,
        'status': 'pending',
        'error_message': None,
        'amount': ['0.00028551', 'BTC'],
        'traded_amount': ['0.0', 'BTC'],
        'total_exchanged': ['0.0', 'USDC']
    }
]

batch_cancellation_buy_limit_flow = {
    'orders_diff': [{'mode': 'cancel', 'order_id': 1366298103}, {'mode': 'cancel', 'order_id': 1366298105}]
}

place_sub_orders_sell_limit_flow_traded = [
    {
        'id': 1367813959,
        'status': 'pending',
        'error_message': None,
        'amount': ['0.00009976', 'BTC'],
        'traded_amount': ['0.0', 'BTC'],
        'total_exchanged': ['0.0', 'USDC']
    },
    {
        'id': 1367813961,
        'status': 'pending',
        'error_message': None,
        'amount': ['0.00004272', 'BTC'],
        'traded_amount': ['0.0', 'BTC'],
        'total_exchanged': ['0.0', 'USDC']
    }
]

states_sub_orders_sell_limit_flow = {"orders": [
    {
        'id': 1367813961, 'uuid': '3f5c4a2b-4ec8-434a-8e13-fc2b211e0017', 'market_id': 'BTC-USDC', 'account_id': 143870,
        'type': 'Ask', 'state': 'traded', 'created_at': '2025-02-08T16:39:04.368Z', 'fee_currency': 'USDC',
        'price_type': 'limit', 'source': None, 'client_id': None, 'message': None, 'order_type': 'gtc', 'expire_at': 0,
        'limit': ['105277.9337', 'USDC'], 'amount': ['0.00004272', 'BTC'], 'original_amount': ['0.00004272', 'BTC'],
        'traded_amount': ['0.00004272', 'BTC'], 'total_exchanged': ['4.5', 'USDC'], 'paid_fee': ['0.0', 'USDC'],
        'stop_price': None
    },
    {
        'id': 1367813959, 'uuid': '3f5c4a2b-4ec8-434a-8e13-fc2b211e0017', 'market_id': 'BTC-USDC', 'account_id': 143870,
        'type': 'Ask', 'state': 'traded', 'created_at': '2025-02-08T16:39:04.368Z', 'fee_currency': 'USDC',
        'price_type': 'limit', 'source': None, 'client_id': None, 'message': None, 'order_type': 'gtc', 'expire_at': 0,
        'limit': ['105277.9337', 'USDC'], 'amount': ['0.00009976', 'BTC'], 'original_amount': ['0.00009976', 'BTC'],
        'traded_amount': ['0.00009976', 'BTC'], 'total_exchanged': ['10.5', 'USDC'], 'paid_fee': ['0.0', 'USDC'],
        'stop_price': None
    }
]
}

batch_cancellation_sell_limit_flow_traded = {
    'orders_diff': [{'mode': 'cancel', 'order_id': 1367813959}, {'mode': 'cancel', 'order_id': 1367813961}]
}

new_order_binance_sell_limit_flow_traded = {
    'symbol': 'BTCUSDC',
    'orderId': 3962637728,
    'orderListId': -1,
    'clientOrderId': 'eWpdt8VN1RZgx0tiqIkFD5',
    'transactTime': 1738333733346,
    'price': '0.00000000',
    'origQty': '0.00014000',
    'executedQty': '0.00014000',
    'origQuoteOrderQty': '0.00000000',
    'cummulativeQuoteQty': '14.64585780',
    'status': 'FILLED',
    'timeInForce': 'GTC',
    'type': 'MARKET',
    'side': 'BUY',
    'workingTime': 1738333733346,
    'fills': [
        {
            'price': '104613.27000000',
            'qty': '0.00014000',
            'commission': '0.00000013',
            'commissionAsset': 'BTC',
            'tradeId': 133249829}
    ],
    'selfTradePreventionMode': 'EXPIRE_MAKER'
}

buda_create_withdraw_request_sell_limit_flow_traded = {
    'id': 'pGwNxJ',
    'uuid': '6b250edc-9871-4223-b761-e9755ca185fe',
    'state': 'executing',
    'currency': 'USDC',
    'created_at': '2025-01-31T15:38:52.355Z',
    'withdrawal_data':
        {
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
    'amount': ['14.996126', 'USDC'],
    'fee': ['1.0', 'USDC'],
    'usd_amount': ['15.02', 'USD']
}

binance_pay_ln_invoice_sell_limit_flow_traded = {'id': 'd8ea0779171a433f8f1e83a5e1892786'}

buda_get_withdraw_history_sell_limit_flow_traded_1 = \
    [{
        'id': 'pGwNxJ',
        'uuid': 'ff8c9b6b-ed36-4a65-93a4-756a29046bbf',
        'state': 'executing',
        'currency': 'USDC',
        'created_at': '2025-01-31T15:09:47.146Z',
        'withdrawal_data':
            {
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
        'amount': ['14.996126', 'USDC'],
        'fee': ['1.0', 'USDC'],
        'usd_amount': ['14.97', 'USD']
    }]


buda_get_withdraw_history_sell_limit_flow_traded_2 = \
    [{
        'id': 'pGwNxJ',
        'uuid': 'ff8c9b6b-ed36-4a65-93a4-756a29046bbf',
        'state': 'confirmed',
        'currency': 'USDC',
        'created_at': '2025-01-31T15:09:47.146Z',
        'withdrawal_data':
            {
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
        'amount': ['14.996126', 'USDC'],
        'fee': ['1.0', 'USDC'],
        'usd_amount': ['14.97', 'USD']
    }]

binance_get_withdraw_history_sell_limit_flow_traded_1 = [{
    'id': 'd8ea0779171a433f8f1e83a5e1892786',
    'amount': '0.000142',
    'transactionFee': '0.000001',
    'coin': 'BTC',
    'status': 4,
    'address': 'lnbc142u1pnee6czpp57k5e65v6hxy76tt8t7ujej7e5jm5hu5jz2at2yrscfxsccvenuzqdqqcqzzsxqyz5vqsp5qwnnream6lr5j4fkjqqn7qlm945j0j4emtv58fpray3jvs5j967s9qxpqysgq34y7cqvlsk8s0p57acvfwgeta6qwhkemnd2a8hkhgdxj8q037pq4mam0r55jel02pcsjp5949tc78r0ccqnqr6j4t2tkdt77z928smsq0r4u9t',
    'txId': 'f5a99d519ab989ed2d675fb92ccbd9a4b74bf29212bab51070c24d0c61999f04',
    'applyTime': '2025-01-31 15:23:47',
    'network': 'LIGHTNING',
    'transferType': 0,
    'info': 'Please note that you will receive an email once it is completed.',
    'walletType': 0,
    'txKey': '',
    'state': 'pending_confirmation'
}]

binance_get_withdraw_history_sell_limit_flow_traded_2 = [{
    'id': 'd8ea0779171a433f8f1e83a5e1892786',
    'amount': '0.000142',
    'transactionFee': '0.000001',
    'coin': 'BTC',
    'status': 4,
    'address': 'lnbc142u1pnee6czpp57k5e65v6hxy76tt8t7ujej7e5jm5hu5jz2at2yrscfxsccvenuzqdqqcqzzsxqyz5vqsp5qwnnream6lr5j4fkjqqn7qlm945j0j4emtv58fpray3jvs5j967s9qxpqysgq34y7cqvlsk8s0p57acvfwgeta6qwhkemnd2a8hkhgdxj8q037pq4mam0r55jel02pcsjp5949tc78r0ccqnqr6j4t2tkdt77z928smsq0r4u9t',
    'txId': 'f5a99d519ab989ed2d675fb92ccbd9a4b74bf29212bab51070c24d0c61999f04',
    'applyTime': '2025-01-31 15:23:47',
    'network': 'LIGHTNING',
    'transferType': 0,
    'info': 'Please note that you will receive an email once it is completed.',
    'walletType': 0,
    'txKey': '',
    'state': 'confirmed'
}]