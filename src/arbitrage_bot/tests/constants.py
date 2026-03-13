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

