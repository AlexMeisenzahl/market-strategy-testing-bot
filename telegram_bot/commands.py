"""
Telegram Bot Command Handlers

Implements bot commands for controlling and monitoring the trading bot:
- /status - Get current bot status
- /stats - Get trading statistics
- /stop - Stop the bot
- /start - Start the bot
"""

from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path


class TelegramCommands:
    """Handler for telegram bot commands"""

    def __init__(self, bot_controller: Optional[Any] = None):
        """
        Initialize command handler

        Args:
            bot_controller: Reference to bot controller for start/stop operations
        """
        self.bot_controller = bot_controller
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Hello {user.first_name}!\n\n"
            "I'm the Market Strategy Testing Bot.\n\n"
            "Available commands:\n"
            "/status - Get current bot status\n"
            "/stats - View trading statistics\n"
            "/stop - Stop the trading bot\n"
            "/start - Start the trading bot\n"
            "/help - Show this help message"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            "📚 *Market Strategy Testing Bot Commands*\n\n"
            "*/status* - Get current bot status and running strategies\n"
            "*/stats* - View detailed trading statistics\n"
            "*/stop* - Stop the trading bot\n"
            "*/start* - Start the trading bot\n"
            "*/help* - Show this help message\n\n"
            "_Use these commands to control and monitor your trading bot._",
            parse_mode="Markdown",
        )

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - show bot status"""
        try:
            status = self._get_bot_status()

            message = f"""🤖 *Bot Status*

Status: {status['status']}
Uptime: {status['uptime']}
Active Strategies: {status['active_strategies']}
Total Capital: ${status['total_capital']:.2f}

📊 *Today's Performance*
P&L: ${status['daily_pnl']:.2f} ({status['daily_pnl_pct']:+.2f}%)
Trades: {status['trades_today']}
Win Rate: {status['win_rate']:.1f}%

Last Updated: {status['last_updated']}"""

            await update.message.reply_text(message, parse_mode="Markdown")

        except Exception as e:
            await update.message.reply_text(
                f"❌ Error getting status: {str(e)}"
            )

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - show detailed statistics"""
        try:
            stats = self._get_trading_stats()

            message = f"""📊 *Trading Statistics*

🎯 *Overall Performance*
Total Trades: {stats['total_trades']}
Win Rate: {stats['win_rate']:.1f}%
Total P&L: ${stats['total_pnl']:.2f}
Avg Trade P&L: ${stats['avg_trade_pnl']:.2f}

📈 *Risk Metrics*
Max Drawdown: {stats['max_drawdown']:.2f}%
Sharpe Ratio: {stats['sharpe_ratio']:.2f}
Profit Factor: {stats['profit_factor']:.2f}

💰 *Best Performers*
Best Trade: ${stats['best_trade']:.2f}
Worst Trade: ${stats['worst_trade']:.2f}

🔥 *Top Strategy*
{stats['top_strategy']}: {stats['top_strategy_pnl']:.2f}%

Last Updated: {stats['last_updated']}"""

            await update.message.reply_text(message, parse_mode="Markdown")

        except Exception as e:
            await update.message.reply_text(
                f"❌ Error getting stats: {str(e)}"
            )

    async def cmd_bot_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command - stop the bot"""
        try:
            if self.bot_controller and hasattr(self.bot_controller, "stop"):
                self.bot_controller.stop()
                await update.message.reply_text(
                    "🛑 *Bot Stopped*\n\n"
                    "Trading bot has been stopped.\n"
                    "Use /start to resume.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "⚠️ Bot controller not available.\n"
                    "Stop the bot manually or via dashboard."
                )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Error stopping bot: {str(e)}"
            )

    async def cmd_bot_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /resume command - resume the bot"""
        try:
            if self.bot_controller and hasattr(self.bot_controller, "start"):
                self.bot_controller.start()
                await update.message.reply_text(
                    "▶️ *Bot Started*\n\n"
                    "Trading bot is now running.\n"
                    "Use /status to check status.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    "⚠️ Bot controller not available.\n"
                    "Start the bot manually or via dashboard."
                )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Error starting bot: {str(e)}"
            )

    def _get_bot_status(self) -> Dict[str, Any]:
        """
        Get current bot status from activity logs

        Returns:
            Dictionary with status information
        """
        try:
            # Load activity log
            activity_log = self.logs_dir / "activity.json"
            if activity_log.exists():
                with open(activity_log, "r") as f:
                    activities = json.load(f)

                # Find last bot_started event
                started_event = None
                for activity in reversed(activities):
                    if activity.get("type") == "bot_started":
                        started_event = activity
                        break

                # Calculate uptime
                uptime = "Unknown"
                if started_event:
                    start_time = datetime.fromisoformat(
                        started_event.get("timestamp", datetime.now().isoformat())
                    )
                    uptime_delta = datetime.now() - start_time.replace(tzinfo=None)
                    hours = uptime_delta.total_seconds() / 3600
                    uptime = f"{hours:.1f} hours"

                # Get today's trades
                today = datetime.now().date()
                trades_today = sum(
                    1
                    for a in activities
                    if a.get("type") == "trade_executed"
                    and datetime.fromisoformat(a.get("timestamp", "")).date() == today
                )

                # Calculate daily P&L (simplified)
                daily_pnl = 0.0
                daily_pnl_pct = 0.0

                return {
                    "status": "🟢 Running" if started_event else "🔴 Stopped",
                    "uptime": uptime,
                    "active_strategies": len(
                        started_event.get("strategies", [])
                    ) if started_event else 0,
                    "total_capital": started_event.get("total_capital", 10000) if started_event else 10000,
                    "daily_pnl": daily_pnl,
                    "daily_pnl_pct": daily_pnl_pct,
                    "trades_today": trades_today,
                    "win_rate": 0.0,  # Would need trade results to calculate
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

            return {
                "status": "🔴 No Data",
                "uptime": "0 hours",
                "active_strategies": 0,
                "total_capital": 10000,
                "daily_pnl": 0.0,
                "daily_pnl_pct": 0.0,
                "trades_today": 0,
                "win_rate": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            print(f"Error getting bot status: {e}")
            return {
                "status": "❌ Error",
                "uptime": "Unknown",
                "active_strategies": 0,
                "total_capital": 0,
                "daily_pnl": 0.0,
                "daily_pnl_pct": 0.0,
                "trades_today": 0,
                "win_rate": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    def _get_trading_stats(self) -> Dict[str, Any]:
        """
        Get trading statistics from trade logs

        Returns:
            Dictionary with trading statistics
        """
        try:
            # Load trades from activity log
            activity_log = self.logs_dir / "activity.json"
            if activity_log.exists():
                with open(activity_log, "r") as f:
                    activities = json.load(f)

                # Filter trade activities
                trades = [a for a in activities if a.get("type") == "trade_executed"]

                total_trades = len(trades)

                # Calculate basic stats (simplified - would need actual P&L data)
                return {
                    "total_trades": total_trades,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "avg_trade_pnl": 0.0,
                    "max_drawdown": 0.0,
                    "sharpe_ratio": 0.0,
                    "profit_factor": 0.0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0,
                    "top_strategy": "N/A",
                    "top_strategy_pnl": 0.0,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_trade_pnl": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "profit_factor": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "top_strategy": "N/A",
                "top_strategy_pnl": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            print(f"Error getting trading stats: {e}")
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_trade_pnl": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "profit_factor": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "top_strategy": "N/A",
                "top_strategy_pnl": 0.0,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
