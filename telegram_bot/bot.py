"""
Telegram Bot Module

Provides Telegram notification functionality for the trading bot.
"""

from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, Any, Optional
import os
from logger import get_logger


class TelegramNotifier:
    """
    Telegram bot for sending notifications

    Handles initialization and message sending via Telegram Bot API.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Telegram bot

        Args:
            config: Configuration dictionary with Telegram settings
        """
        self.config = config
        self.logger = get_logger()

        # Extract configuration
        self.enabled = config.get("enabled", False)
        bot_token = config.get("bot_token", "")
        self.chat_id = config.get("chat_id", "")

        # Initialize bot
        if not self.enabled:
            self.bot = None
            self.logger.log_info("Telegram notifications disabled")
            return

        if not bot_token or bot_token == "${TELEGRAM_BOT_TOKEN}":
            self.logger.log_warning("Telegram bot token not configured")
            self.bot = None
            self.enabled = False
            return

        if not self.chat_id or self.chat_id == "${TELEGRAM_CHAT_ID}":
            self.logger.log_warning("Telegram chat ID not configured")
            self.bot = None
            self.enabled = False
            return

        try:
            self.bot = Bot(token=bot_token)
            self.logger.log_info("Telegram bot initialized successfully")

            # Test connection
            self._test_connection()

        except Exception as e:
            self.logger.log_error(f"Failed to initialize Telegram bot: {e}")
            self.bot = None
            self.enabled = False

    def _test_connection(self) -> bool:
        """
        Test Telegram bot connection

        Returns:
            True if connection is successful
        """
        if not self.bot:
            return False

        try:
            # Get bot info
            bot_info = self.bot.get_me()
            self.logger.log_info(f"Telegram bot connected: @{bot_info.username}")
            return True
        except Exception as e:
            self.logger.log_error(f"Telegram connection test failed: {e}")
            return False

    def is_enabled(self) -> bool:
        """Check if Telegram notifications are enabled"""
        return self.enabled and self.bot is not None

    def should_send_notification(self, notification_type: str) -> bool:
        """
        Check if a notification type should be sent

        Args:
            notification_type: Type of notification

        Returns:
            True if notification should be sent
        """
        if not self.is_enabled():
            return False

        notifications_config = self.config.get("notifications", {})
        return notifications_config.get(notification_type, False)

    async def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False,
    ) -> bool:
        """
        Send a message via Telegram

        Args:
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)
            disable_notification: Whether to send silently

        Returns:
            True if message was sent successfully
        """
        if not self.is_enabled():
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
            )
            return True

        except TelegramError as e:
            self.logger.log_error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            self.logger.log_error(f"Unexpected error sending Telegram message: {e}")
            return False

    def send_message_sync(
        self,
        message: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False,
    ) -> bool:
        """
        Send a message via Telegram (synchronous)

        Args:
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)
            disable_notification: Whether to send silently

        Returns:
            True if message was sent successfully
        """
        if not self.is_enabled():
            return False

        try:
            import requests

            url = f"https://api.telegram.org/bot{self.bot.token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification,
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            return True

        except Exception as e:
            self.logger.log_error(f"Failed to send Telegram message: {e}")
            return False


def create_telegram_bot(config: Dict[str, Any]) -> Optional[TelegramNotifier]:
    """
    Create and initialize Telegram bot

    Args:
        config: Configuration dictionary

    Returns:
        TelegramNotifier instance or None if disabled
    """
    telegram_config = config.get("telegram", {})

    if not telegram_config.get("enabled", False):
        return None

    return TelegramNotifier(telegram_config)
