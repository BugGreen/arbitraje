import unittest
from unittest.mock import patch
import requests
import time
from src.exchange_api.utils import retry_with_exponential_backoff  # Adjust the import to your actual module


class TestRetryWithExponentialBackoff(unittest.TestCase):

    @patch('src.exchange_api.utils.requests.get')
    def test_request_exception_with_no_response(self, mock_get):
        """Test for request exception with no response (RemoteDisconnected)"""
        mock_get.side_effect = requests.exceptions.RequestException("Remote connection closed without response")

        with self.assertRaises(Exception) as context:
            retry_with_exponential_backoff(mock_get)

        self.assertTrue('Failed after' in str(context.exception))

    @patch('src.exchange_api.utils.requests.get')
    def test_request_exception_with_response(self, mock_get):
        """Test for request exception with a response object (502, 524, etc.)"""
        mock_response = requests.Response()
        mock_response.status_code = 502
        mock_get.side_effect = requests.exceptions.RequestException("API Error", response=mock_response)

        with self.assertRaises(Exception) as context:
            retry_with_exponential_backoff(mock_get)

        self.assertTrue('Failed after' in str(context.exception))

    @patch('src.exchange_api.utils.requests.get')
    def test_successful_request(self, mock_get):
        """Test for successful request (no exception)"""
        mock_get.return_value = "Success"

        result = retry_with_exponential_backoff(mock_get)

        self.assertEqual(result, "Success")


if __name__ == '__main__':
    unittest.main()
