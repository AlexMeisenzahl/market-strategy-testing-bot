#!/usr/bin/env python3
"""
Main Bot Runner - 24/7 Strategy Execution Engine

This is the core bot loop that:
- Initializes all 4 strategies (Arbitrage, Momentum, News, StatisticalArb)
- Runs strategies continuously every 60 seconds
- Logs ALL opportunities found (even if not traded)
- Executes best opportunities via paper trading
- Updates dashboard data files
- Handles graceful shutdown

Usage:
    python run_bot.py
"""

import sys
import signal
import time
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from logger import get_logger
from strategy_manager import StrategyManager
from services.paper_trading_engine import PaperTradingEngine
from polymarket_api import PolymarketAPI
from services.secure_config_manager import SecureConfigManager
from config.config_loader import get_config
from services.data_flow_manager import DataFlowManager
from clients import (
    PolymarketClient,
    CoinGeckoClient,
    MockMarketClient,
    MockCryptoClient,
)
import os
import requests

# Import all available strategies
from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.news_strategy import NewsStrategy
from strategies.volatility_breakout_strategy import VolatilityBreakoutStrategy
from strategies.weather_trading import WeatherTradingStrategy
from strategies.btc_arbitrage import BTCArbitrageStrategy
from strategies.polymarket_arbitrage import PolymarketArbitrageStrategy
from strategies.statistical_arb_strategy import StatisticalArbStrategy
from strategies.contrarian_strategy import ContrarianStrategy


class SimpleTelegramBot:
    """Simple synchronous telegram bot for notifications"""
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, text: str) -> bool:
        """Send a message via telegram API"""
        try:
            url = f"{self.base_url}/sendMessage"
            response = requests.post(
                url, 
                json={'chat_id': self.chat_id, 'text': text, 'parse_mode': 'Markdown'}, 
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            # Silently fail, don't crash the bot
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test telegram API connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {'success': True, 'bot_name': data['result'].get('username', 'Unknown')}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class BotRunner:
    """Main bot runner that orchestrates all strategies and trading"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the bot runner

        Args:
            config_path: Path to configuration file
        """
        self.logger = get_logger()
        self.running = False

        # Load configuration using ConfigLoader (ENV > YAML > DEFAULT)
        try:
            config_loader = get_config(config_path=config_path)
            self.config_loader = config_loader

            # Convert to dict for backward compatibility
            self.config = self._load_config_from_loader(config_loader, config_path)

            env_name = config_loader.get("trading_bot_env", "development")
            self.logger.log_warning(f"Configuration loaded: ENVIRONMENT={env_name}")
        except Exception as e:
            self.logger.log_error(f"Failed to load config via ConfigLoader: {e}")
            # Fallback to old method
            self.config = self._load_config(config_path)
            self.config_loader = None

        # Initialize core components
        self.strategy_manager = StrategyManager(self.config)
        self.paper_trader = PaperTradingEngine(self.config)
        self.polymarket_api = PolymarketAPI(
            timeout=self.config.get("api_timeout_seconds", 10),
            retry_attempts=self.config.get("api_retry_attempts", 3),
        )

        # Initialize data flow manager for dashboard updates
        self.data_flow_manager = DataFlowManager(self.config)

        # Initialize data clients (market and crypto data)
        self.market_client, self.crypto_client = self._initialize_data_clients()

        # Initialize risk manager for position sizing and limits
        from services.risk_manager import get_risk_manager

        self.risk_manager = get_risk_manager(self.config)

        # Initialize settings manager for configuration persistence
        from services.settings_manager import get_settings_manager
        
        self.settings_manager = get_settings_manager(config_path)
        
        # Get cycle interval from settings (default 60 seconds)
        self.cycle_interval = self.settings_manager.get_setting('bot.cycle_interval', 60)

        # Initialize alert system for custom alerts
        from services.alert_system import get_alert_system

        self.alert_system = get_alert_system(self.config)

        # Initialize telegram bot for notifications (simple sync version)
        self.telegram_bot = None
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

        if telegram_token and telegram_chat_id:
            try:
                self.telegram_bot = SimpleTelegramBot(token=telegram_token, chat_id=telegram_chat_id)
                # Test connection
                test_result = self.telegram_bot.test_connection()
                if test_result['success']:
                    self.logger.log_info(f"✅ Telegram bot initialized: @{test_result.get('bot_name', 'Unknown')}")
                else:
                    self.logger.log_warning(f"⚠️ Telegram bot failed: {test_result.get('error', 'Unknown error')}")
                    self.telegram_bot = None
            except Exception as e:
                self.logger.log_warning(f"⚠️ Telegram bot failed: {e}")
                self.telegram_bot = None
        else:
            self.logger.log_warning("⚠️ Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")

        # Setup directories
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.activity_log_path = self.logs_dir / "activity.json"

        # Statistics
        self.start_time = datetime.now(timezone.utc)
        self.cycles_completed = 0
        self.total_opportunities_found = 0
        self.total_trades_executed = 0
        self.total_opportunities_skipped = 0

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.log_warning("=" * 60)
        self.logger.log_warning("🚀 Market Strategy Testing Bot - Starting Up")
        self.logger.log_warning("=" * 60)

    def _load_config_from_loader(
        self, config_loader, config_path: str
    ) -> Dict[str, Any]:
        """
        Load configuration from ConfigLoader and merge with YAML config.
        Environment variables take precedence over YAML.

        Args:
            config_loader: ConfigLoader instance
            config_path: Path to YAML config file

        Returns:
            Merged configuration dictionary
        """
        # Start with YAML config if it exists
        config = self._load_config(config_path)

        # Override with environment variables where applicable
        env_overrides = {
            "paper_trading": config_loader.get("paper_trading"),
            "debug": config_loader.get("debug"),
            "log_level": config_loader.get("log_level"),
            "api_timeout_seconds": config_loader.get("request_timeout", 30),
            "max_trade_size": config_loader.get("max_trade_size"),
            "min_profit_margin": config_loader.get("min_profit_margin"),
        }

        # Apply overrides only if values are different from defaults
        for key, value in env_overrides.items():
            if value is not None:
                config[key] = value

        # Merge feature flags
        feature_flags = config_loader.get_feature_flags()
        if "feature_flags" not in config:
            config["feature_flags"] = {}
        config["feature_flags"].update(feature_flags)

        return config

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(config_path)

        # If config.yaml doesn't exist, try config.example.yaml
        if not config_file.exists():
            config_file = Path("config.example.yaml")
            if not config_file.exists():
                self.logger.log_error("No configuration file found!")
                raise FileNotFoundError("No config.yaml or config.example.yaml found")

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Set default strategies if not configured
        if "strategies" not in config:
            config["strategies"] = {
                "enabled": ["arbitrage", "momentum", "news", "statistical_arb"]
            }

        return config

    def _initialize_data_clients(self):
        """
        Initialize market and crypto data clients based on API configuration

        Returns:
            Tuple of (market_client, crypto_client)
        """
        config_manager = SecureConfigManager()

        # Initialize Market Client (Polymarket or Mock)
        market_client = None
        if config_manager.has_polymarket_api():
            self.logger.log_warning(
                "🔗 Polymarket API configured, attempting connection..."
            )
            creds = config_manager.get_api_credentials("polymarket")
            try:
                endpoint = creds.get("endpoint", "https://clob.polymarket.com")
                api_key = creds.get("api_key")
                market_client = PolymarketClient(endpoint=endpoint, api_key=api_key)

                # Test connection
                result = market_client.test_connection()
                if result["success"]:
                    self.logger.log_warning(f"✅ {result['message']}")
                    self.logger.log_warning("📊 Using LIVE Polymarket data")
                else:
                    self.logger.log_warning(
                        f"⚠️  Polymarket connection failed: {result['error']}"
                    )
                    self.logger.log_warning("📊 Falling back to MOCK market data")
                    market_client = None
            except Exception as e:
                self.logger.log_warning(
                    f"⚠️  Error initializing Polymarket client: {str(e)}"
                )
                self.logger.log_warning("📊 Falling back to MOCK market data")
                market_client = None

        # Use mock client if no live client
        if market_client is None:
            self.logger.log_warning(
                "📊 No Polymarket API configured - Using MOCK market data"
            )
            market_client = MockMarketClient()
            market_client.connect()

        # Initialize Crypto Client (CoinGecko or Mock)
        crypto_client = None
        if config_manager.has_crypto_api():
            self.logger.log_warning(
                "🔗 Crypto API configured, attempting connection..."
            )
            creds = config_manager.get_api_credentials("crypto")
            try:
                provider = creds.get("provider", "coingecko")
                if provider == "coingecko":
                    endpoint = creds.get("endpoint", "https://api.coingecko.com/api/v3")
                    api_key = creds.get("api_key")
                    crypto_client = CoinGeckoClient(endpoint=endpoint, api_key=api_key)

                    # Test connection
                    result = crypto_client.test_connection()
                    if result["success"]:
                        self.logger.log_warning(f"✅ {result['message']}")
                        self.logger.log_warning("💰 Using LIVE crypto price data")
                    else:
                        self.logger.log_warning(
                            f"⚠️  Crypto API connection failed: {result['error']}"
                        )
                        self.logger.log_warning("💰 Falling back to MOCK crypto data")
                        crypto_client = None
            except Exception as e:
                self.logger.log_warning(
                    f"⚠️  Error initializing crypto client: {str(e)}"
                )
                self.logger.log_warning("💰 Falling back to MOCK crypto data")
                crypto_client = None

        # Use mock client if no live client
        if crypto_client is None:
            self.logger.log_warning(
                "💰 No crypto API configured - Using MOCK crypto data"
            )
            crypto_client = MockCryptoClient()
            crypto_client.connect()

        return market_client, crypto_client

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.log_warning(
            "\n🛑 Shutdown signal received. Stopping bot gracefully..."
        )
        self.running = False

    def _log_activity(self, activity: Dict[str, Any]) -> None:
        """
        Log activity to activity.json for dashboard consumption

        Args:
            activity: Activity data to log
        """
        try:
            # Load existing activities
            activities = []
            if self.activity_log_path.exists():
                with open(self.activity_log_path, "r") as f:
                    try:
                        activities = json.load(f)
                        if not isinstance(activities, list):
                            activities = []
                    except json.JSONDecodeError:
                        activities = []

            # Add timestamp if not present
            if "timestamp" not in activity:
                activity["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Append new activity
            activities.append(activity)

            # Keep only last 1000 activities to prevent file from growing too large
            activities = activities[-1000:]

            # Write back to file
            with open(self.activity_log_path, "w") as f:
                json.dump(activities, f, indent=2)

        except Exception as e:
            self.logger.log_error(f"Failed to log activity: {str(e)}")

    def _fetch_markets(self) -> List[Dict[str, Any]]:
        """
        Fetch current markets using configured data client

        Returns:
            List of market data dictionaries
        """
        try:
            # Use the configured market client (live or mock)
            markets = self.market_client.get_markets(min_volume=1000, limit=100)

            if markets:
                market_type = (
                    "LIVE"
                    if isinstance(self.market_client, PolymarketClient)
                    else "MOCK"
                )
                self.logger.log_warning(
                    f"📊 Fetched {len(markets)} {market_type} markets"
                )

                # Convert to expected format if needed
                return self._normalize_market_format(markets)
            else:
                self.logger.log_warning("⚠️  No markets returned, using mock data")
                return self._get_mock_markets()

        except Exception as e:
            self.logger.log_warning(f"⚠️  Error fetching markets: {str(e)}")
            self.logger.log_warning("📊 Falling back to mock market data")
            return self._get_mock_markets()

    def _normalize_market_format(
        self, markets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Normalize market format to ensure consistency

        Args:
            markets: Raw market data from client

        Returns:
            Normalized market data
        """
        normalized = []
        for market in markets:
            # Ensure all required fields exist
            normalized.append(
                {
                    "id": market.get("market_id", market.get("id", "unknown")),
                    "question": market.get(
                        "market_name", market.get("question", "Unknown")
                    ),
                    "yes_price": market.get("yes_price", 0.5),
                    "no_price": market.get("no_price", 0.5),
                    "liquidity": market.get("liquidity", 0),
                    "volume_24h": market.get("volume_24h", 0),
                    "category": market.get("category", "unknown"),
                }
            )
        return normalized

    def _get_mock_markets(self) -> List[Dict[str, Any]]:
        """
        Generate mock market data for testing when API is unavailable

        Returns:
            List of mock market dictionaries
        """
        # Create markets with various profit margins for testing
        markets = []

        # High profit opportunity (should be executed)
        markets.append(
            {
                "id": "0x123456789abcdef",
                "question": "Will Bitcoin reach $100k by March 2026?",
                "yes_price": 0.45,
                "no_price": 0.52,  # Sum: 0.97 (3% arbitrage margin - realistic edge case)
                "liquidity": 50000,
                "volume_24h": 12000,
                "category": "crypto",
            }
        )

        # Low profit opportunity (should be skipped)
        markets.append(
            {
                "id": "0x234567890abcdef",
                "question": "Will Ethereum surpass $3000 in February 2026?",
                "yes_price": 0.62,
                "no_price": 0.37,  # 0.62 + 0.37 = 0.99 (1% margin - below threshold)
                "liquidity": 75000,
                "volume_24h": 25000,
                "category": "crypto",
            }
        )

        # Medium profit opportunity
        markets.append(
            {
                "id": "0x345678901abcdef",
                "question": "Will the Fed cut interest rates in Q1 2026?",
                "yes_price": 0.48,
                "no_price": 0.49,  # 0.48 + 0.49 = 0.97 (3% margin)
                "liquidity": 100000,
                "volume_24h": 35000,
                "category": "politics",
            }
        )

        # Another low profit (should be skipped)
        markets.append(
            {
                "id": "0x456789012abcdef",
                "question": "Will S&P 500 reach new high in February?",
                "yes_price": 0.51,
                "no_price": 0.48,  # 0.51 + 0.48 = 0.99 (1% margin)
                "liquidity": 80000,
                "volume_24h": 20000,
                "category": "finance",
            }
        )

        # High profit opportunity
        markets.append(
            {
                "id": "0x567890123abcdef",
                "question": "Will Solana hit $200 by March 2026?",
                "yes_price": 0.44,
                "no_price": 0.51,  # 0.44 + 0.51 = 0.95 (5% margin)
                "liquidity": 60000,
                "volume_24h": 18000,
                "category": "crypto",
            }
        )

        return markets

    def _convert_markets_to_prices_dict(
        self, markets: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Convert markets list to prices dictionary format

        Args:
            markets: List of market dictionaries

        Returns:
            Dictionary mapping market_id to price data
        """
        prices_dict = {}
        for market in markets:
            market_id = market.get("id", "")
            prices_dict[market_id] = {
                "yes": market.get("yes_price", 0.5),
                "no": market.get("no_price", 0.5),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        return prices_dict

    def _process_opportunities(self, all_opportunities: Dict[str, List[Any]]) -> None:
        """
        Process opportunities from all strategies, logging each one

        Args:
            all_opportunities: Dictionary mapping strategy name to list of opportunities
        """
        for strategy_name, opportunities in all_opportunities.items():
            for opp in opportunities:
                self.total_opportunities_found += 1

                # Convert opportunity to dict for logging
                opp_dict = opp.to_dict() if hasattr(opp, "to_dict") else {}

                # Determine if we should trade
                # Note: profit_margin from strategy is expected to be in percentage form (e.g., 3.0 for 3%)
                profit_margin = (
                    opp.profit_margin if hasattr(opp, "profit_margin") else 0
                )
                min_margin = (
                    self.config.get("min_profit_margin", 0.02) * 100
                )  # Convert 0.02 to 2.0%

                should_trade = profit_margin >= min_margin

                if should_trade:
                    # Log opportunity that will be executed
                    self._log_activity(
                        {
                            "type": "opportunity_found",
                            "strategy": strategy_name,
                            "confidence": opp_dict.get("confidence", profit_margin),
                            "market_id": opp_dict.get("market_id", ""),
                            "market_name": opp_dict.get("market_name", ""),
                            "yes_price": opp_dict.get("yes_price", 0),
                            "no_price": opp_dict.get("no_price", 0),
                            "profit_margin": profit_margin,
                            "action": "executing",
                            "reason": f"Meets {min_margin:.1f}% minimum threshold",
                        }
                    )
                else:
                    # Log opportunity that was skipped
                    self.total_opportunities_skipped += 1
                    self._log_activity(
                        {
                            "type": "opportunity_found",
                            "strategy": strategy_name,
                            "confidence": opp_dict.get("confidence", profit_margin),
                            "market_id": opp_dict.get("market_id", ""),
                            "market_name": opp_dict.get("market_name", ""),
                            "yes_price": opp_dict.get("yes_price", 0),
                            "no_price": opp_dict.get("no_price", 0),
                            "profit_margin": profit_margin,
                            "action": "skipped",
                            "reason": f"Below {min_margin:.1f}% minimum threshold",
                        }
                    )

    def _execute_trades(self, all_opportunities: Dict[str, List[Any]]) -> None:
        """
        Execute trades for opportunities that meet criteria

        Args:
            all_opportunities: Dictionary mapping strategy name to list of opportunities
        """
        trades_executed = self.strategy_manager.execute_best_opportunities(
            all_opportunities
        )

        for strategy_name, count in trades_executed.items():
            if count > 0:
                self.total_trades_executed += count
                self.logger.log_warning(f"⚡ {strategy_name}: Executed {count} trades")

                # Send telegram notification for trade
                if self.telegram_bot:
                    # Get opportunity details for notification
                    opps = all_opportunities.get(strategy_name, [])
                    for opp in opps[:count]:  # Send notification for executed trades
                        opp_dict = opp.to_dict() if hasattr(opp, "to_dict") else {}
                        profit_margin = opp.profit_margin if hasattr(opp, "profit_margin") else 0
                        
                        message = f"""🔔 *Trade Executed*

Strategy: {strategy_name}
Market: {opp_dict.get('market_name', 'Unknown')}
Confidence: {profit_margin:.2f}%
Action: BUY
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"""
                        
                        self.telegram_bot.send_message(message)

                # Log trade execution
                self._log_activity(
                    {
                        "type": "trade_executed",
                        "strategy": strategy_name,
                        "count": count,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

        # Process signals through data flow manager for dashboard updates
        for strategy_name, opportunities in all_opportunities.items():
            for opp in opportunities:
                # Convert opportunity to signal format
                opp_dict = opp.to_dict() if hasattr(opp, "to_dict") else {}

                # Only process opportunities that meet threshold
                profit_margin = (
                    opp.profit_margin if hasattr(opp, "profit_margin") else 0
                )
                min_margin = self.config.get("min_profit_margin", 0.02) * 100

                if profit_margin >= min_margin:
                    signal = {
                        "action": "BUY",  # Default action
                        "symbol": opp_dict.get(
                            "market_id", opp_dict.get("market_name", "")
                        ),
                        "market_id": opp_dict.get("market_id", ""),
                        "price": opp_dict.get("yes_price", 0.5),
                        "quantity": 1,  # Default quantity
                        "confidence": profit_margin,
                        "strategy": strategy_name,
                    }

                    # Process signal through data flow manager
                    self.data_flow_manager.process_signal(strategy_name, signal)

    def _check_alerts(
        self, markets: List[Dict[str, Any]], prices_dict: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Check all configured alerts against current market data

        Args:
            markets: List of market data
            prices_dict: Dictionary of prices by market_id
        """
        try:
            # Prepare alert data with prices and portfolio metrics
            portfolio_value = self.paper_trader.get_total_value() if hasattr(self.paper_trader, 'get_total_value') else 10000
            
            # Calculate daily P&L percentage from paper trader if available
            daily_pnl_percent = 0.0
            if hasattr(self.paper_trader, 'get_daily_pnl_percent'):
                daily_pnl_percent = self.paper_trader.get_daily_pnl_percent()
            
            alert_data = {
                'portfolio_value': portfolio_value,
                'daily_pnl_percent': daily_pnl_percent,
                'prices': {market_id: price_data.get('yes', 0.5) for market_id, price_data in prices_dict.items()},
                'trade_executed': False
            }

            # Get custom alert manager and check alerts
            from services.alert_manager import alert_manager
            triggered = alert_manager.check_alerts(alert_data)
            
            for alert in triggered:
                alert_message = alert.get('message', 'Alert triggered')
                self.logger.log_warning(f"🚨 Alert: {alert_message}")
                
                # Send telegram notification if available
                if self.telegram_bot:
                    self.telegram_bot.send_message(f"🚨 {alert_message}")
                
                # Log to activity
                self._log_activity(
                    {
                        "type": "alert_triggered",
                        "alert_id": alert.get('id'),
                        "message": alert_message,
                    }
                )

        except Exception as e:
            self.logger.log_error(f"Error checking alerts: {e}")

    def _check_risk_positions(self, prices_dict: Dict[str, Dict[str, float]]) -> None:
        """
        Check risk limits and update open positions

        Args:
            prices_dict: Dictionary of prices by market_id
        """
        try:
            # Extract current prices for position updates
            current_prices = {
                market_id: price_data.get("yes", 0.5)
                for market_id, price_data in prices_dict.items()
            }

            # Check all positions for stop-loss/take-profit triggers
            actions = self.risk_manager.check_all_positions(current_prices)

            # Log triggered actions
            for market_id, action in actions:
                self.logger.log_warning(f"⚠️ Risk trigger for {market_id}: {action}")

                # Log to activity
                self._log_activity(
                    {
                        "type": "risk_trigger",
                        "market_id": market_id,
                        "action": action,
                    }
                )

            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary()

            # Log if close to daily loss limit
            if risk_summary["daily_loss"] > risk_summary["daily_loss_limit"] * 0.8:
                self.logger.log_warning(
                    f"⚠️ Daily loss at {risk_summary['daily_loss']:.2f} "
                    f"(limit: {risk_summary['daily_loss_limit']:.2f})"
                )

        except Exception as e:
            self.logger.log_error(f"Error checking risk positions: {e}")

    def _check_exit_conditions(self, prices_dict: Dict[str, Dict[str, float]]) -> None:
        """
        Check if any open positions should be exited

        Args:
            prices_dict: Dictionary of prices by market_id
        """
        try:
            # Extract current prices
            current_prices = {
                market_id: price_data.get("yes", 0.5)
                for market_id, price_data in prices_dict.items()
            }

            # Check for exit conditions (stop-loss/take-profit)
            for position in self.risk_manager.get_all_positions():
                market_id = position["market_id"]

                if market_id in current_prices:
                    current_price = current_prices[market_id]

                    # Check if position should be closed
                    action = self.risk_manager.check_stop_loss_take_profit(
                        market_id, current_price
                    )

                    if action:
                        # Close position
                        closed_position = self.risk_manager.close_position(
                            market_id, current_price
                        )

                        if closed_position:
                            self.logger.log_warning(
                                f"💰 Position closed ({action}): {market_id} "
                                f"P&L: ${closed_position['realized_pnl']:.2f}"
                            )

                            # Log to activity
                            self._log_activity(
                                {
                                    "type": "position_closed",
                                    "market_id": market_id,
                                    "action": action,
                                    "pnl": closed_position["realized_pnl"],
                                }
                            )

        except Exception as e:
            self.logger.log_error(f"Error checking exit conditions: {e}")

    def run_cycle(self) -> None:
        """Run a single bot cycle"""
        try:
            self.cycles_completed += 1
            self.logger.log_warning(f"\n{'=' * 60}")
            self.logger.log_warning(
                f"🔄 Cycle #{self.cycles_completed} - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            self.logger.log_warning(f"{'=' * 60}")

            # 1. Fetch markets
            markets = self._fetch_markets()
            prices_dict = self._convert_markets_to_prices_dict(markets)

            # 2. Check alerts with current market data
            self._check_alerts(markets, prices_dict)

            # 3. Check risk limits and open positions
            self._check_risk_positions(prices_dict)

            # 4. Run all strategies to find opportunities
            all_opportunities = self.strategy_manager.run_all_strategies(
                markets, prices_dict
            )

            # 5. Process and log all opportunities (even if not traded)
            self._process_opportunities(all_opportunities)

            # 6. Execute best opportunities (paper trades) with risk checks
            self._execute_trades(all_opportunities)

            # 7. Check open positions for exits (stop-loss/take-profit)
            self._check_exit_conditions(prices_dict)

            # 8. Log cycle summary
            total_opps_this_cycle = sum(
                len(opps) for opps in all_opportunities.values()
            )
            self.logger.log_warning(
                f"📊 Cycle Summary: {total_opps_this_cycle} opportunities found, "
                f"{self.total_trades_executed} total trades executed"
            )

        except Exception as e:
            self.logger.log_error(f"❌ Error in bot cycle: {str(e)}")
            self.logger.log_error(traceback.format_exc())

            # Log error activity
            self._log_activity(
                {
                    "type": "error",
                    "message": str(e),
                    "traceback": traceback.format_exc()[
                        :500
                    ],  # Truncate long tracebacks
                }
            )

    def run(self) -> None:
        """Main bot loop - runs continuously until stopped"""
        self.running = True

        # Print startup banner
        self.logger.log_warning("📊 Loaded 4 strategies:")
        for strategy_name in self.strategy_manager.strategies.keys():
            self.logger.log_warning(f"   ✓ {strategy_name}")

        self.logger.log_warning(
            f"💰 Total Capital: ${self.strategy_manager.total_capital}"
        )
        self.logger.log_warning(
            f"📝 Paper Trading Mode: {'ENABLED' if self.config.get('paper_trading', True) else 'DISABLED'}"
        )
        self.logger.log_warning("🔄 Scanning markets every 60 seconds...")
        self.logger.log_warning("Press CTRL+C to stop\n")

        # Log startup activity
        self._log_activity(
            {
                "type": "bot_started",
                "mode": "paper" if self.config.get("paper_trading", True) else "live",
                "strategies": list(self.strategy_manager.strategies.keys()),
                "total_capital": self.strategy_manager.total_capital,
            }
        )

        # Main loop
        while self.running:
            try:
                # Run one cycle
                self.run_cycle()

                # Wait before next cycle (use configured interval)
                if self.running:  # Check again in case we were stopped during cycle
                    self.logger.log_warning(
                        f"\n⏳ Waiting {self.cycle_interval} seconds until next scan...\n"
                    )
                    time.sleep(self.cycle_interval)

            except KeyboardInterrupt:
                self.logger.log_warning("\n🛑 Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.log_error(f"❌ Unexpected error in main loop: {str(e)}")
                self.logger.log_error(traceback.format_exc())

                # Wait before retrying to avoid rapid error loops
                if self.running:
                    time.sleep(10)

        # Shutdown
        self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shutdown the bot"""
        self.logger.log_warning("\n" + "=" * 60)
        self.logger.log_warning("🛑 Bot Shutdown Summary")
        self.logger.log_warning("=" * 60)

        runtime = datetime.now(timezone.utc) - self.start_time
        hours = runtime.total_seconds() / 3600

        self.logger.log_warning(f"⏱️  Runtime: {hours:.2f} hours")
        self.logger.log_warning(f"🔄 Cycles completed: {self.cycles_completed}")
        self.logger.log_warning(
            f"🔍 Opportunities found: {self.total_opportunities_found}"
        )
        self.logger.log_warning(f"⚡ Trades executed: {self.total_trades_executed}")
        self.logger.log_warning(
            f"⏭️  Opportunities skipped: {self.total_opportunities_skipped}"
        )
        self.logger.log_warning("=" * 60)

        # Log shutdown activity
        self._log_activity(
            {
                "type": "bot_stopped",
                "runtime_hours": hours,
                "cycles_completed": self.cycles_completed,
                "total_opportunities": self.total_opportunities_found,
                "total_trades": self.total_trades_executed,
                "opportunities_skipped": self.total_opportunities_skipped,
            }
        )

        self.logger.log_warning("👋 Bot stopped. Goodbye!")


def main():
    """Main entry point"""
    logger = None
    try:
        # Initialize logger first to ensure we can log errors
        logger = get_logger()
        logger.log_info("=" * 60)
        logger.log_info("🤖 Market Strategy Testing Bot - Starting")
        logger.log_info("=" * 60)

        # Initialize and run the bot
        bot = BotRunner()
        bot.run()

    except FileNotFoundError as e:
        error_msg = f"❌ Configuration file not found: {str(e)}"
        if logger:
            logger.log_error(error_msg)
        else:
            print(error_msg)
        print("\n💡 Tip: Make sure config.yaml exists in the current directory")
        print("   You can copy config.example.yaml to config.yaml to get started")
        traceback.print_exc()
        sys.exit(1)

    except ImportError as e:
        error_msg = f"❌ Missing dependency: {str(e)}"
        if logger:
            logger.log_error(error_msg)
        else:
            print(error_msg)
        print("\n💡 Tip: Install dependencies with: pip install -r requirements.txt")
        traceback.print_exc()
        sys.exit(1)

    except KeyError as e:
        error_msg = f"❌ Configuration error - missing key: {str(e)}"
        if logger:
            logger.log_error(error_msg)
        else:
            print(error_msg)
        print("\n💡 Tip: Check your config.yaml for missing required fields")
        print("   Compare with config.example.yaml for reference")
        traceback.print_exc()
        sys.exit(1)

    except KeyboardInterrupt:
        msg = "\n\n🛑 Bot stopped by user (Ctrl+C)"
        if logger:
            logger.log_warning(msg)
        else:
            print(msg)
        sys.exit(0)

    except Exception as e:
        error_msg = f"❌ Fatal error: {str(e)}"
        if logger:
            logger.log_error(error_msg)
        else:
            print(error_msg)
        print("\n💡 Check the logs for more details")
        print("   Run with FLASK_DEBUG=true for verbose output")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
