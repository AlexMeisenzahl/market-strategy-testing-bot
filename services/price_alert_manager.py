"""
Price Alert Manager - Monitor crypto price thresholds

Monitors cryptocurrency prices and triggers alerts when thresholds are crossed.
Supports above/below thresholds and percentage change alerts.

Example alerts:
    - BTC crosses above $100,000
    - ETH drops below $3,000
    - SOL changes by more than 10% from baseline
"""

import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.crypto_price_manager import CryptoPriceManager


class PriceAlertManager:
    """
    Manage price alerts for cryptocurrencies

    Features:
    - Monitor multiple price thresholds
    - Support above/below/change_pct alert types
    - Prevent duplicate notifications
    - Auto-reset after price moves away
    - Configurable check intervals
    """

    def __init__(self, logger=None, config: Dict = None):
        """
        Initialize price alert manager

        Args:
            logger: Logger instance
            config: Configuration dictionary
        """
        self.logger = logger
        self.config = config or {}

        # Initialize price manager
        self.price_manager = CryptoPriceManager(logger=logger, config=config)

        # Load alert configuration
        alert_config = self.config.get("price_alerts", {})
        self.enabled = alert_config.get("enabled", True)
        self.check_interval = alert_config.get("check_interval_seconds", 30)
        self.alerts = alert_config.get("alerts", [])

        # Track triggered alerts to prevent duplicates
        self.triggered_alerts: Set[str] = set()
        self.trigger_times: Dict[str, datetime] = {}
        self.reset_delay = timedelta(minutes=5)  # Reset after 5 minutes

        # Baseline prices for change_pct alerts
        self.baseline_prices: Dict[str, Decimal] = {}

        self.last_check_time = 0

    def check_alerts(self) -> List[Dict]:
        """
        Check all configured alerts and return triggered ones

        Returns:
            List of triggered alert dictionaries

        Example:
            >>> manager = PriceAlertManager(logger=logger, config=config)
            >>> triggered = manager.check_alerts()
            >>> for alert in triggered:
            ...     print(f"🚨 ALERT: {alert['symbol']} crossed {alert['threshold']}")
        """
        if not self.enabled:
            return []

        # Rate limit checks
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return []

        self.last_check_time = current_time

        # Get symbols we need to check
        symbols = list(set(alert["symbol"] for alert in self.alerts))

        if not symbols:
            return []

        # Fetch current prices
        current_prices = self.price_manager.get_current_prices(symbols)

        if not current_prices:
            if self.logger:
                self.logger.log_warning("Failed to fetch prices for alert checking")
            return []

        triggered = []

        # Check each alert
        for alert in self.alerts:
            symbol = alert["symbol"]
            alert_type = alert["type"]
            threshold = Decimal(str(alert["threshold"]))

            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]["price_usd"]

            # Generate alert key for duplicate prevention
            alert_key = f"{symbol}_{alert_type}_{threshold}"

            # Check if this alert was recently triggered
            if alert_key in self.triggered_alerts:
                # Check if we should reset it
                trigger_time = self.trigger_times.get(alert_key)
                if trigger_time and datetime.now() - trigger_time > self.reset_delay:
                    # Check if price has moved away from threshold
                    if self._should_reset_alert(alert_type, current_price, threshold):
                        self.triggered_alerts.remove(alert_key)
                        del self.trigger_times[alert_key]
                        if self.logger:
                            self.logger.log_info(f"Reset alert: {alert_key}")
                else:
                    # Still in cooldown, skip this alert
                    continue

            # Check alert condition
            is_triggered = False

            if alert_type == "above":
                is_triggered = current_price > threshold
            elif alert_type == "below":
                is_triggered = current_price < threshold
            elif alert_type == "change_pct":
                # Check percentage change from baseline
                if symbol not in self.baseline_prices:
                    # Set baseline on first check
                    self.baseline_prices[symbol] = current_price
                    continue

                baseline = self.baseline_prices[symbol]
                change_pct = abs((current_price - baseline) / baseline * 100)
                is_triggered = change_pct >= threshold

            if is_triggered:
                # Alert triggered!
                self.triggered_alerts.add(alert_key)
                self.trigger_times[alert_key] = datetime.now()

                triggered_alert = {
                    "symbol": symbol,
                    "type": alert_type,
                    "threshold": float(threshold),
                    "current_price": float(current_price),
                    "notification": alert.get("notification", True),
                    "timestamp": datetime.now().isoformat(),
                }

                if alert_type == "change_pct":
                    baseline = self.baseline_prices[symbol]
                    change_pct = (current_price - baseline) / baseline * 100
                    triggered_alert["baseline_price"] = float(baseline)
                    triggered_alert["change_pct"] = float(change_pct)

                triggered.append(triggered_alert)

                if self.logger:
                    if alert_type == "above":
                        self.logger.log_info(
                            f"🚨 PRICE ALERT: {symbol} crossed above ${threshold:,.0f} (now ${current_price:,.0f})"
                        )
                    elif alert_type == "below":
                        self.logger.log_info(
                            f"🚨 PRICE ALERT: {symbol} dropped below ${threshold:,.0f} (now ${current_price:,.0f})"
                        )
                    elif alert_type == "change_pct":
                        self.logger.log_info(
                            f"🚨 PRICE ALERT: {symbol} changed {change_pct:+.1f}% (now ${current_price:,.0f})"
                        )

        return triggered

    def _should_reset_alert(
        self, alert_type: str, current_price: Decimal, threshold: Decimal
    ) -> bool:
        """
        Determine if an alert should be reset based on current conditions

        Args:
            alert_type: Type of alert
            current_price: Current price
            threshold: Alert threshold

        Returns:
            True if alert should be reset
        """
        # Reset if price has moved away from threshold by at least 2%
        reset_margin = Decimal("0.02")

        if alert_type == "above":
            # Reset if price drops below threshold
            return current_price < threshold * (1 - reset_margin)
        elif alert_type == "below":
            # Reset if price rises above threshold
            return current_price > threshold * (1 + reset_margin)
        elif alert_type == "change_pct":
            # Always reset change_pct alerts after cooldown
            return True

        return False

    def add_alert(
        self, symbol: str, alert_type: str, threshold: float, notification: bool = True
    ) -> None:
        """
        Add a new alert

        Args:
            symbol: Crypto symbol
            alert_type: 'above', 'below', or 'change_pct'
            threshold: Price threshold or percentage
            notification: Whether to send notifications
        """
        alert = {
            "symbol": symbol,
            "type": alert_type,
            "threshold": threshold,
            "notification": notification,
        }

        # Check if alert already exists
        for existing in self.alerts:
            if (
                existing["symbol"] == symbol
                and existing["type"] == alert_type
                and abs(existing["threshold"] - threshold) < 0.01
            ):
                # Alert already exists
                return

        self.alerts.append(alert)

        if self.logger:
            self.logger.log_info(
                f"Added price alert: {symbol} {alert_type} {threshold}"
            )

    def remove_alert(self, symbol: str, alert_type: str, threshold: float) -> bool:
        """
        Remove an alert

        Args:
            symbol: Crypto symbol
            alert_type: 'above', 'below', or 'change_pct'
            threshold: Price threshold or percentage

        Returns:
            True if alert was found and removed
        """
        for i, alert in enumerate(self.alerts):
            if (
                alert["symbol"] == symbol
                and alert["type"] == alert_type
                and abs(alert["threshold"] - threshold) < 0.01
            ):
                self.alerts.pop(i)

                if self.logger:
                    self.logger.log_info(
                        f"Removed price alert: {symbol} {alert_type} {threshold}"
                    )

                return True

        return False

    def get_active_alerts(self) -> List[Dict]:
        """
        Get list of all active alerts

        Returns:
            List of alert dictionaries
        """
        return self.alerts.copy()

    def reset_baselines(self) -> None:
        """Reset baseline prices for change_pct alerts"""
        self.baseline_prices.clear()

        if self.logger:
            self.logger.log_info("Reset price alert baselines")
