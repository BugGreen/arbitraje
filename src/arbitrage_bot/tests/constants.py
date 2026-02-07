expected_insolvent_error_response = {
    "error_code": "INSUFFICIENT_FUNDS",
    "message": "One or more sub-orders could not be processed (insolvent).",
    "sub_order": {
        'id': None,
        'status': 'unprepared',
        'error_message': 'insolvent',
        'amount': ['1.001000001', 'ETH']}
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