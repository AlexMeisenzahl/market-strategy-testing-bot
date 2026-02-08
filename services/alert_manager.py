"""
Custom Alert Manager

Manages user-defined alerts for price movements, strategy signals,
and portfolio thresholds.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from database.models import Alert
from services.notification_service import notification_service


class AlertManager:
    """
    Custom alert manager

    Alert types:
    - price: Trigger when price crosses threshold
    - strategy: Trigger when strategy detects opportunity
    - portfolio: Trigger when portfolio metrics reach threshold
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Alert Manager initialized")

    def create_alert(
        self, alert_type: str, condition: Dict, enabled: bool = True
    ) -> int:
        """
        Create a new alert

        Args:
            alert_type: 'price', 'strategy', or 'portfolio'
            condition: Alert condition dict
            enabled: Whether alert is enabled

        Returns:
            Alert ID

        Examples:
            # Price alert
            alert_id = alert_manager.create_alert(
                'price',
                {'symbol': 'BTC', 'threshold': 100000, 'direction': 'above'}
            )

            # Strategy alert
            alert_id = alert_manager.create_alert(
                'strategy',
                {'strategy': 'momentum', 'min_confidence': 0.8}
            )

            # Portfolio alert
            alert_id = alert_manager.create_alert(
                'portfolio',
                {'metric': 'total_value', 'threshold': 15000, 'direction': 'above'}
            )
        """
        # Validate alert type
        if alert_type not in ["price", "strategy", "portfolio"]:
            raise ValueError(f"Invalid alert type: {alert_type}")

        # Validate condition
        self._validate_condition(alert_type, condition)

        # Create alert
        condition_json = json.dumps(condition)
        alert_id = Alert.create(alert_type, condition_json, enabled)

        self.logger.info(f"Alert created: #{alert_id} ({alert_type}) - {condition}")

        return alert_id

    def update_alert(self, alert_id: int, enabled: bool = None, condition: Dict = None):
        """
        Update an existing alert

        Args:
            alert_id: Alert ID
            enabled: New enabled status
            condition: New condition dict
        """
        if condition:
            condition_json = json.dumps(condition)
        else:
            condition_json = None

        Alert.update(alert_id, enabled, condition_json)

        self.logger.info(f"Alert updated: #{alert_id}")

    def delete_alert(self, alert_id: int):
        """
        Delete an alert

        Args:
            alert_id: Alert ID
        """
        Alert.delete(alert_id)
        self.logger.info(f"Alert deleted: #{alert_id}")

    def check_alerts(self, current_data: Dict = None) -> List[Dict]:
        """
        Check all enabled alerts and trigger if conditions met

        Args:
            current_data: Current market/portfolio data

        Returns:
            List of triggered alerts
        """
        enabled_alerts = Alert.get_enabled()

        if not enabled_alerts:
            return []

        triggered = []

        for alert in enabled_alerts:
            alert_type = alert["alert_type"]
            condition = json.loads(alert["condition_json"])

            # Check if alert should trigger
            should_trigger = False

            if alert_type == "price":
                should_trigger = self._check_price_alert(condition, current_data)
            elif alert_type == "strategy":
                should_trigger = self._check_strategy_alert(condition, current_data)
            elif alert_type == "portfolio":
                should_trigger = self._check_portfolio_alert(condition, current_data)

            if should_trigger:
                # Record trigger
                Alert.record_trigger(alert["id"])

                # Send notification
                self._send_alert_notification(alert, condition)

                triggered.append(
                    {
                        "alert_id": alert["id"],
                        "alert_type": alert_type,
                        "condition": condition,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                self.logger.info(f"Alert triggered: #{alert['id']} ({alert_type})")

        return triggered

    def _check_price_alert(self, condition: Dict, current_data: Dict) -> bool:
        """
        Check if price alert should trigger

        Args:
            condition: Alert condition
            current_data: Current market data

        Returns:
            True if should trigger
        """
        if not current_data or "prices" not in current_data:
            return False

        symbol = condition.get("symbol")
        threshold = condition.get("threshold")
        direction = condition.get("direction", "above")

        prices = current_data["prices"]
        current_price = prices.get(symbol)

        if current_price is None:
            return False

        if direction == "above":
            return current_price > threshold
        elif direction == "below":
            return current_price < threshold

        return False

    def _check_strategy_alert(self, condition: Dict, current_data: Dict) -> bool:
        """
        Check if strategy alert should trigger

        Args:
            condition: Alert condition
            current_data: Current market data

        Returns:
            True if should trigger
        """
        if not current_data or "opportunities" not in current_data:
            return False

        strategy = condition.get("strategy")
        min_confidence = condition.get("min_confidence", 0.5)

        opportunities = current_data["opportunities"]

        # Check if any opportunity matches criteria
        for opp in opportunities:
            if opp.get("strategy") == strategy:
                if opp.get("confidence", 0) >= min_confidence:
                    return True

        return False

    def _check_portfolio_alert(self, condition: Dict, current_data: Dict) -> bool:
        """
        Check if portfolio alert should trigger

        Args:
            condition: Alert condition
            current_data: Current portfolio data

        Returns:
            True if should trigger
        """
        if not current_data or "portfolio" not in current_data:
            return False

        metric = condition.get("metric")
        threshold = condition.get("threshold")
        direction = condition.get("direction", "above")

        portfolio = current_data["portfolio"]
        current_value = portfolio.get(metric)

        if current_value is None:
            return False

        if direction == "above":
            return current_value > threshold
        elif direction == "below":
            return current_value < threshold

        return False

    def _validate_condition(self, alert_type: str, condition: Dict):
        """
        Validate alert condition

        Args:
            alert_type: Alert type
            condition: Condition dict

        Raises:
            ValueError if condition is invalid
        """
        if alert_type == "price":
            required = ["symbol", "threshold", "direction"]
            for field in required:
                if field not in condition:
                    raise ValueError(f"Price alert missing field: {field}")

            if condition["direction"] not in ["above", "below"]:
                raise ValueError(f"Invalid direction: {condition['direction']}")

        elif alert_type == "strategy":
            if "strategy" not in condition:
                raise ValueError("Strategy alert missing 'strategy' field")

        elif alert_type == "portfolio":
            required = ["metric", "threshold"]
            for field in required:
                if field not in condition:
                    raise ValueError(f"Portfolio alert missing field: {field}")

    def _send_alert_notification(self, alert: Dict, condition: Dict):
        """
        Send alert notification

        Args:
            alert: Alert dict
            condition: Condition dict
        """
        alert_type = alert["alert_type"]

        # Format message
        if alert_type == "price":
            message = (
                f"Price Alert: {condition['symbol']} is "
                f"{condition['direction']} ${condition['threshold']}"
            )
        elif alert_type == "strategy":
            message = (
                f"Strategy Alert: {condition['strategy']} " f"opportunity detected"
            )
        elif alert_type == "portfolio":
            message = (
                f"Portfolio Alert: {condition['metric']} is "
                f"{condition['direction']} {condition['threshold']}"
            )
        else:
            message = f"Alert triggered: {alert_type}"

        # Send notification (if notification service available)
        try:
            if notification_service:
                notification_service.send_notification(
                    title="Custom Alert Triggered", message=message, level="info"
                )
        except Exception as e:
            self.logger.warning(f"Failed to send alert notification: {e}")

    def get_all_alerts(self) -> List[Dict]:
        """
        Get all alerts

        Returns:
            List of alert dicts
        """
        alerts = Alert.get_all()

        # Parse condition JSON
        for alert in alerts:
            alert["condition"] = json.loads(alert["condition_json"])

        return alerts

    def get_alert_statistics(self) -> Dict:
        """
        Get alert statistics

        Returns:
            Dict with alert stats
        """
        alerts = Alert.get_all()
        enabled_alerts = Alert.get_enabled()

        # Count by type
        type_counts = {}
        for alert in alerts:
            alert_type = alert["alert_type"]
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1

        # Get most triggered
        most_triggered = sorted(
            alerts, key=lambda a: a.get("trigger_count", 0), reverse=True
        )[:5]

        return {
            "total_alerts": len(alerts),
            "enabled_alerts": len(enabled_alerts),
            "disabled_alerts": len(alerts) - len(enabled_alerts),
            "alerts_by_type": type_counts,
            "most_triggered": [
                {
                    "id": a["id"],
                    "type": a["alert_type"],
                    "trigger_count": a.get("trigger_count", 0),
                }
                for a in most_triggered
            ],
        }

    def test_alert(self, alert_id: int, test_data: Dict) -> Dict:
        """
        Test an alert with sample data

        Args:
            alert_id: Alert ID
            test_data: Test data to check against

        Returns:
            Dict with test result
        """
        alerts = Alert.get_all()
        alert = next((a for a in alerts if a["id"] == alert_id), None)

        if not alert:
            return {"success": False, "error": f"Alert {alert_id} not found"}

        alert_type = alert["alert_type"]
        condition = json.loads(alert["condition_json"])

        # Check if would trigger
        should_trigger = False

        if alert_type == "price":
            should_trigger = self._check_price_alert(condition, test_data)
        elif alert_type == "strategy":
            should_trigger = self._check_strategy_alert(condition, test_data)
        elif alert_type == "portfolio":
            should_trigger = self._check_portfolio_alert(condition, test_data)

        return {
            "success": True,
            "alert_id": alert_id,
            "alert_type": alert_type,
            "condition": condition,
            "would_trigger": should_trigger,
            "test_data": test_data,
        }


# Global instance
alert_manager = AlertManager()
