from src.telegram_bot.telegram_alert import TelegramAlert
from unittest.mock import patch, MagicMock
import unittest
import asyncio


class TestTelegramAlert(unittest.TestCase):

    @patch("src.telegram_bot.telegram_alert.TelegramAlert.send_message")
    def test_send_message(self, mock_send_message):
        # Arrange
        mock_send_message.return_value = MagicMock()  # Simulate successful response
        bot_token = "test_bot_token"
        chat_id = "test_chat_id"
        message = "Test message"

        telegram_alert = TelegramAlert()

        # Act
        asyncio.run(telegram_alert.send_message(message))

        # Assert
        mock_send_message.assert_called_once_with(message)

    # @patch("src.telegram_bot.telegram_alert.TelegramAlert.send_message")
    # def test_send_message_error(self, mock_send_message):
    #     # Arrange
    #     mock_send_message.side_effect = Exception("Error sending message")  # Simulate an error
    #     bot_token = "test_bot_token"
    #     chat_id = "test_chat_id"
    #     message = "Test message"
    #
    #     telegram_alert = TelegramAlert()
    #
    #     # Act
    #     asyncio.run(telegram_alert.send_message(message))
    #
    #     # Assert
    #     mock_send_message.assert_called_once_with(message)
    #     # You can also check logger.error was called if you mock the logger


if __name__ == "__main__":
    unittest.main()
