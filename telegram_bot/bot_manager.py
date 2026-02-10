"""
Telegram Bot Manager

Manages the telegram bot lifecycle, including:
- Bot initialization and shutdown
- Command registration
- Daily summary scheduling
- Error handling
"""

import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, time, timedelta
from telegram import Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.error import TelegramError
import logging

from telegram_bot.commands import TelegramCommands
from telegram_bot.notifications import TelegramNotifications

logger = logging.getLogger(__name__)


class TelegramBotManager:
    """
    Manages telegram bot application and commands

    Handles bot lifecycle, command registration, and scheduled messages.
    """

    def __init__(self, config: Dict[str, Any], bot_controller: Optional[Any] = None):
        """
        Initialize telegram bot manager

        Args:
            config: Configuration dictionary with telegram settings
            bot_controller: Optional reference to bot controller for start/stop
        """
        self.config = config
        self.bot_controller = bot_controller

        # Extract telegram configuration
        telegram_config = config.get("telegram", {})
        self.enabled = telegram_config.get("enabled", False)
        self.bot_token = telegram_config.get("bot_token", "")
        self.chat_id = telegram_config.get("chat_id", "")

        # Replace environment variable placeholders
        if self.bot_token.startswith("${") and self.bot_token.endswith("}"):
            env_var = self.bot_token[2:-1]
            self.bot_token = os.getenv(env_var, "")

        if self.chat_id.startswith("${") and self.chat_id.endswith("}"):
            env_var = self.chat_id[2:-1]
            self.chat_id = os.getenv(env_var, "")

        self.application: Optional[Application] = None
        self.commands: Optional[TelegramCommands] = None
        self.notifications: Optional[TelegramNotifications] = None
        self._daily_summary_task: Optional[asyncio.Task] = None

    def is_configured(self) -> bool:
        """
        Check if telegram is properly configured

        Returns:
            True if bot token and chat ID are set
        """
        return bool(
            self.enabled
            and self.bot_token
            and self.chat_id
            and not self.bot_token.startswith("${")
            and not self.chat_id.startswith("${")
        )

    async def initialize(self) -> bool:
        """
        Initialize the telegram bot application

        Returns:
            True if initialization succeeded
        """
        if not self.is_configured():
            logger.warning("Telegram bot not configured, skipping initialization")
            return False

        try:
            # Create application
            self.application = Application.builder().token(self.bot_token).build()

            # Initialize command handler
            self.commands = TelegramCommands(bot_controller=self.bot_controller)

            # Register command handlers
            self.application.add_handler(
                CommandHandler("start", self.commands.cmd_start)
            )
            self.application.add_handler(CommandHandler("help", self.commands.cmd_help))
            self.application.add_handler(
                CommandHandler("status", self.commands.cmd_status)
            )
            self.application.add_handler(
                CommandHandler("stats", self.commands.cmd_stats)
            )
            self.application.add_handler(
                CommandHandler("stop", self.commands.cmd_bot_stop)
            )

            # Initialize application
            await self.application.initialize()
            await self.application.start()

            # Test connection
            bot = self.application.bot
            bot_info = await bot.get_me()
            logger.info(f"Telegram bot connected: @{bot_info.username}")

            # Send startup message
            await self._send_startup_message()

            # Schedule daily summary if enabled
            if (
                self.config.get("telegram", {})
                .get("notifications", {})
                .get("daily_summary", False)
            ):
                await self._schedule_daily_summary()

            logger.info("Telegram bot manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize telegram bot: {e}")
            return False

    async def shutdown(self):
        """Shutdown the telegram bot gracefully"""
        try:
            # Cancel daily summary task
            if self._daily_summary_task and not self._daily_summary_task.done():
                self._daily_summary_task.cancel()
                try:
                    await self._daily_summary_task
                except asyncio.CancelledError:
                    pass

            # Send shutdown message
            await self._send_shutdown_message()

            # Stop application
            if self.application:
                await self.application.stop()
                await self.application.shutdown()

            logger.info("Telegram bot manager shut down successfully")

        except Exception as e:
            logger.error(f"Error shutting down telegram bot: {e}")

    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message via telegram bot

        Args:
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)

        Returns:
            True if message sent successfully
        """
        if not self.application:
            return False

        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            return True

        except TelegramError as e:
            logger.error(f"Failed to send telegram message: {e}")
            return False

    async def send_trade_alert(
        self,
        market_name: str,
        direction: str,
        size: float,
        price: float,
        strategy: Optional[str] = None,
    ) -> bool:
        """
        Send a trade execution alert

        Args:
            market_name: Market name
            direction: Trade direction (buy/sell)
            size: Trade size
            price: Execution price
            strategy: Strategy name

        Returns:
            True if alert sent successfully
        """
        strategy_text = f"\nStrategy: {strategy}" if strategy else ""

        message = f"""🤖 *Trade Executed*

Market: {market_name}
Direction: {direction.upper()}
Size: ${size:.2f}
Price: {price:.4f}{strategy_text}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        return await self.send_message(message)

    async def send_error_alert(self, error_type: str, error_message: str) -> bool:
        """
        Send an error alert

        Args:
            error_type: Type of error
            error_message: Error message

        Returns:
            True if alert sent successfully
        """
        message = f"""⚠️ *Error Alert*

Type: {error_type}
Message: {error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        return await self.send_message(message)

    async def send_daily_summary(
        self,
        trades_count: int = 0,
        pnl: float = 0.0,
        pnl_pct: float = 0.0,
        win_rate: float = 0.0,
    ) -> bool:
        """
        Send daily trading summary

        Args:
            trades_count: Number of trades
            pnl: Daily P&L
            pnl_pct: Daily P&L percentage
            win_rate: Win rate percentage

        Returns:
            True if summary sent successfully
        """
        emoji = "📊"

        message = f"""{emoji} *Daily Summary*

Trades: {trades_count}
P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)
Win Rate: {win_rate:.1f}%

Date: {datetime.now().strftime('%Y-%m-%d')}"""

        return await self.send_message(message)

    async def _send_startup_message(self):
        """Send bot startup notification"""
        try:
            message = "🟢 *Bot Started*\n\nTrading bot is now running.\nUse /status to check status."
            await self.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")

    async def _send_shutdown_message(self):
        """Send bot shutdown notification"""
        try:
            message = "🔴 *Bot Stopped*\n\nTrading bot has been stopped."
            await self.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send shutdown message: {e}")

    async def _schedule_daily_summary(self):
        """Schedule daily summary to be sent at configured time"""
        try:
            # Get configured time (default to 20:00)
            summary_config = self.config.get("telegram", {}).get("daily_summary", {})
            hour = summary_config.get("hour", 20)
            minute = summary_config.get("minute", 0)

            async def daily_summary_loop():
                """Send daily summary at configured time"""
                while True:
                    # Calculate time until next summary
                    now = datetime.now()
                    target_time = now.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )

                    if now >= target_time:
                        # If past target time today, schedule for tomorrow
                        target_time = target_time + timedelta(days=1)

                    sleep_seconds = (target_time - now).total_seconds()

                    logger.info(f"Next daily summary in {sleep_seconds/3600:.1f} hours")
                    await asyncio.sleep(sleep_seconds)

                    # Send daily summary
                    await self.send_daily_summary()

            # Start the daily summary task
            self._daily_summary_task = asyncio.create_task(daily_summary_loop())
            logger.info(f"Daily summary scheduled for {hour:02d}:{minute:02d}")

        except Exception as e:
            logger.error(f"Failed to schedule daily summary: {e}")


async def create_bot_manager(
    config: Dict[str, Any], bot_controller: Optional[Any] = None
) -> Optional[TelegramBotManager]:
    """
    Create and initialize telegram bot manager

    Args:
        config: Configuration dictionary
        bot_controller: Optional bot controller reference

    Returns:
        Initialized TelegramBotManager or None if not configured
    """
    manager = TelegramBotManager(config, bot_controller)

    if not manager.is_configured():
        return None

    success = await manager.initialize()
    if not success:
        return None

    return manager
