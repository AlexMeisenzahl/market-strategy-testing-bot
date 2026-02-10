"""
Alert System

Manages custom alerts for price, P&L, trade, and strategy events.
Provides alert configuration storage, trigger logic, and checking.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts"""

    PRICE = "price"
    PNL = "pnl"
    TRADE = "trade"
    STRATEGY = "strategy"
    PORTFOLIO = "portfolio"


class AlertCondition(Enum):
    """Alert condition operators"""

    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    CHANGE_PCT = "change_pct"


class AlertSystem:
    """
    Alert system for managing and triggering custom alerts

    Handles alert configuration, storage, and trigger logic.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize alert system

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.alerts_file = self.data_dir / "alerts.json"
        self.alerts: List[Dict[str, Any]] = []
        self.load_alerts()

    def load_alerts(self):
        """Load alerts from storage"""
        try:
            if self.alerts_file.exists():
                with open(self.alerts_file, "r") as f:
                    self.alerts = json.load(f)
                logger.info(f"Loaded {len(self.alerts)} alerts")
            else:
                self.alerts = []
                self.save_alerts()
        except Exception as e:
            logger.error(f"Failed to load alerts: {e}")
            self.alerts = []

    def save_alerts(self):
        """Save alerts to storage"""
        try:
            with open(self.alerts_file, "w") as f:
                json.dump(self.alerts, f, indent=2)
            logger.debug("Alerts saved successfully")
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")

    def create_alert(
        self,
        alert_type: str,
        name: str,
        condition: str,
        value: float,
        enabled: bool = True,
        notification_channels: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new alert

        Args:
            alert_type: Type of alert (price, pnl, trade, strategy, portfolio)
            name: Alert name
            condition: Condition operator (above, below, equals, change_pct)
            value: Threshold value
            enabled: Whether alert is enabled
            notification_channels: List of notification channels to use
            metadata: Additional metadata (market_id, strategy_name, etc.)

        Returns:
            Created alert dictionary
        """
        alert_id = self._generate_alert_id()

        alert = {
            "id": alert_id,
            "type": alert_type,
            "name": name,
            "condition": condition,
            "value": value,
            "enabled": enabled,
            "notification_channels": notification_channels or ["telegram"],
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0,
        }

        self.alerts.append(alert)
        self.save_alerts()

        logger.info(f"Created alert: {name} ({alert_type})")
        return alert

    def update_alert(
        self, alert_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing alert

        Args:
            alert_id: Alert ID
            updates: Dictionary of fields to update

        Returns:
            Updated alert or None if not found
        """
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert.update(updates)
                self.save_alerts()
                logger.info(f"Updated alert: {alert_id}")
                return alert

        logger.warning(f"Alert not found: {alert_id}")
        return None

    def delete_alert(self, alert_id: str) -> bool:
        """
        Delete an alert

        Args:
            alert_id: Alert ID

        Returns:
            True if deleted successfully
        """
        original_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if a["id"] != alert_id]

        if len(self.alerts) < original_count:
            self.save_alerts()
            logger.info(f"Deleted alert: {alert_id}")
            return True

        logger.warning(f"Alert not found: {alert_id}")
        return False

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific alert

        Args:
            alert_id: Alert ID

        Returns:
            Alert dictionary or None if not found
        """
        for alert in self.alerts:
            if alert["id"] == alert_id:
                return alert
        return None

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all alerts

        Returns:
            List of alert dictionaries
        """
        return self.alerts.copy()

    def get_enabled_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all enabled alerts

        Returns:
            List of enabled alert dictionaries
        """
        return [a for a in self.alerts if a.get("enabled", True)]

    def check_alerts(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check all enabled alerts against current market data

        Args:
            market_data: Current market data including prices, positions, P&L

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        for alert in self.get_enabled_alerts():
            if self._check_alert_condition(alert, market_data):
                triggered_alerts.append(alert)
                self._record_trigger(alert)

        return triggered_alerts

    def _check_alert_condition(
        self, alert: Dict[str, Any], market_data: Dict[str, Any]
    ) -> bool:
        """
        Check if alert condition is met

        Args:
            alert: Alert configuration
            market_data: Current market data

        Returns:
            True if condition is met
        """
        alert_type = alert["type"]
        condition = alert["condition"]
        value = alert["value"]
        metadata = alert.get("metadata", {})

        try:
            if alert_type == AlertType.PRICE.value:
                # Check price alerts
                market_id = metadata.get("market_id")
                if not market_id:
                    return False

                current_price = (
                    market_data.get("prices", {}).get(market_id, {}).get("yes", 0)
                )

                return self._evaluate_condition(current_price, condition, value)

            elif alert_type == AlertType.PNL.value:
                # Check P&L alerts
                current_pnl = market_data.get("portfolio", {}).get("total_pnl", 0)

                return self._evaluate_condition(current_pnl, condition, value)

            elif alert_type == AlertType.PORTFOLIO.value:
                # Check portfolio alerts (total value, exposure, etc.)
                metric = metadata.get("metric", "total_value")
                current_value = market_data.get("portfolio", {}).get(metric, 0)

                return self._evaluate_condition(current_value, condition, value)

            elif alert_type == AlertType.STRATEGY.value:
                # Check strategy performance alerts
                strategy_name = metadata.get("strategy_name")
                if not strategy_name:
                    return False

                strategy_pnl = (
                    market_data.get("strategies", {})
                    .get(strategy_name, {})
                    .get("pnl", 0)
                )

                return self._evaluate_condition(strategy_pnl, condition, value)

            elif alert_type == AlertType.TRADE.value:
                # Check trade alerts (new trade executed, large trade, etc.)
                # This would be triggered directly when trades occur
                return False

            return False

        except Exception as e:
            logger.error(f"Error checking alert condition: {e}")
            return False

    def _evaluate_condition(
        self, current: float, condition: str, threshold: float
    ) -> bool:
        """
        Evaluate alert condition

        Args:
            current: Current value
            condition: Condition operator
            threshold: Threshold value

        Returns:
            True if condition is met
        """
        if condition == AlertCondition.ABOVE.value:
            return current > threshold
        elif condition == AlertCondition.BELOW.value:
            return current < threshold
        elif condition == AlertCondition.EQUALS.value:
            return abs(current - threshold) < 0.01  # Allow small float variance
        elif condition == AlertCondition.CHANGE_PCT.value:
            # For percentage change, threshold is the change %
            # Would need historical data to calculate
            return False

        return False

    def _record_trigger(self, alert: Dict[str, Any]):
        """
        Record that an alert was triggered

        Args:
            alert: Alert that was triggered
        """
        alert["last_triggered"] = datetime.now().isoformat()
        alert["trigger_count"] = alert.get("trigger_count", 0) + 1
        self.save_alerts()

    def _generate_alert_id(self) -> str:
        """
        Generate unique alert ID

        Returns:
            Alert ID string
        """
        return str(uuid.uuid4())[:8]

    def test_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test an alert configuration

        Args:
            alert: Alert configuration to test

        Returns:
            Test result dictionary
        """
        try:
            # Validate alert structure
            required_fields = ["type", "name", "condition", "value"]
            for field in required_fields:
                if field not in alert:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}",
                    }

            # Validate alert type
            if alert["type"] not in [t.value for t in AlertType]:
                return {
                    "success": False,
                    "error": f"Invalid alert type: {alert['type']}",
                }

            # Validate condition
            if alert["condition"] not in [c.value for c in AlertCondition]:
                return {
                    "success": False,
                    "error": f"Invalid condition: {alert['condition']}",
                }

            return {
                "success": True,
                "message": "Alert configuration is valid",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Global instance
alert_system: Optional[AlertSystem] = None


def get_alert_system(config: Optional[Dict[str, Any]] = None) -> AlertSystem:
    """
    Get or create global alert system instance

    Args:
        config: Configuration dictionary (required for first call)

    Returns:
        AlertSystem instance
    """
    global alert_system

    if alert_system is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        alert_system = AlertSystem(config)

    return alert_system
