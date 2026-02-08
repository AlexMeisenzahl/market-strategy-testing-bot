"""
Audit Logging Service

Tracks all important actions for compliance and debugging.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from database.settings_models import get_connection

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Service for logging user actions and system events.
    """

    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger(__name__)

    def log_action(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """
        Log an audit event.

        Args:
            user_id: User performing the action
            action: Action name (e.g., 'settings_updated', 'strategy_enabled')
            entity_type: Type of entity (e.g., 'user_settings', 'notification_channel')
            entity_id: ID of entity affected
            old_value: Previous value (will be JSON serialized)
            new_value: New value (will be JSON serialized)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Audit log entry ID
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Serialize values to JSON
            old_value_json = json.dumps(old_value) if old_value is not None else None
            new_value_json = json.dumps(new_value) if new_value is not None else None

            cursor.execute(
                """
                INSERT INTO audit_log
                (user_id, action, entity_type, entity_id, old_value, new_value, 
                 ip_address, user_agent, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    action,
                    entity_type,
                    entity_id,
                    old_value_json,
                    new_value_json,
                    ip_address,
                    user_agent,
                    datetime.utcnow().isoformat(),
                ),
            )

            conn.commit()
            audit_id = cursor.lastrowid

            self.logger.debug(
                f"Audit log: user={user_id} action={action} entity={entity_type}/{entity_id}"
            )

            return audit_id

        except Exception as e:
            self.logger.error(f"Error logging audit entry: {e}")
            return -1

    def log_settings_change(
        self,
        user_id: int,
        setting_name: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None,
    ) -> int:
        """
        Log a settings change.

        Args:
            user_id: User ID
            setting_name: Name of setting changed
            old_value: Old value
            new_value: New value
            ip_address: Client IP

        Returns:
            Audit log entry ID
        """
        return self.log_action(
            user_id=user_id,
            action="settings_updated",
            entity_type="user_settings",
            entity_id=setting_name,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )

    def log_strategy_change(
        self,
        user_id: int,
        strategy_name: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """
        Log a strategy-related action.

        Args:
            user_id: User ID
            strategy_name: Name of strategy
            action: Action (e.g., 'enabled', 'disabled', 'configured')
            details: Additional details
            ip_address: Client IP

        Returns:
            Audit log entry ID
        """
        return self.log_action(
            user_id=user_id,
            action=f"strategy_{action}",
            entity_type="strategy",
            entity_id=strategy_name,
            new_value=details,
            ip_address=ip_address,
        )

    def log_notification_change(
        self,
        user_id: int,
        channel_type: str,
        action: str,
        old_config: Optional[Dict[str, Any]] = None,
        new_config: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """
        Log a notification channel change.

        Args:
            user_id: User ID
            channel_type: Type of channel
            action: Action (e.g., 'created', 'updated', 'deleted')
            old_config: Old configuration
            new_config: New configuration
            ip_address: Client IP

        Returns:
            Audit log entry ID
        """
        # Sanitize sensitive data
        if old_config:
            old_config = self._sanitize_config(old_config.copy())
        if new_config:
            new_config = self._sanitize_config(new_config.copy())

        return self.log_action(
            user_id=user_id,
            action=f"notification_{action}",
            entity_type="notification_channel",
            entity_id=channel_type,
            old_value=old_config,
            new_value=new_config,
            ip_address=ip_address,
        )

    def log_trading_mode_change(
        self,
        user_id: int,
        old_mode: str,
        new_mode: str,
        ip_address: Optional[str] = None,
    ) -> int:
        """
        Log a trading mode change (critical for safety).

        Args:
            user_id: User ID
            old_mode: Old trading mode
            new_mode: New trading mode
            ip_address: Client IP

        Returns:
            Audit log entry ID
        """
        return self.log_action(
            user_id=user_id,
            action="trading_mode_changed",
            entity_type="system_config",
            entity_id="trading_mode",
            old_value=old_mode,
            new_value=new_mode,
            ip_address=ip_address,
        )

    def get_recent_logs(
        self,
        user_id: Optional[int] = None,
        limit: int = 100,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> list:
        """
        Get recent audit logs.

        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of logs to return
            action: Filter by action (optional)
            entity_type: Filter by entity type (optional)

        Returns:
            List of audit log entries
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Build query
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []

            if user_id is not None:
                query += " AND user_id = ?"
                params.append(user_id)

            if action:
                query += " AND action = ?"
                params.append(action)

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            logs = []
            for row in rows:
                log_entry = dict(row)
                # Parse JSON values
                if log_entry.get("old_value"):
                    try:
                        log_entry["old_value"] = json.loads(log_entry["old_value"])
                    except:
                        pass
                if log_entry.get("new_value"):
                    try:
                        log_entry["new_value"] = json.loads(log_entry["new_value"])
                    except:
                        pass
                logs.append(log_entry)

            return logs

        except Exception as e:
            self.logger.error(f"Error fetching audit logs: {e}")
            return []

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from config before logging.

        Args:
            config: Configuration dictionary

        Returns:
            Sanitized config
        """
        sensitive_keys = [
            "api_key",
            "bot_token",
            "password",
            "smtp_password",
            "webhook_url",
            "secret",
            "token",
        ]

        for key in sensitive_keys:
            if key in config:
                config[key] = "***REDACTED***"

        return config


# Global instance
audit_logger = AuditLogger()
