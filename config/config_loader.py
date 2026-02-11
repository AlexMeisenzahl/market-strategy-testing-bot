"""
Configuration Loader with Environment Variable Priority

Loads configuration with the following precedence (highest to lowest):
1. Environment variables
2. YAML configuration file
3. Default values

This allows for flexible deployment across different environments.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Configuration loader that supports multiple sources with precedence:
    ENV > YAML > DEFAULT
    """

    # Default configuration values
    DEFAULTS = {
        # Application
        "trading_bot_env": "development",
        "debug": False,
        "log_level": "INFO",
        "log_format": "json",
        # Dashboard
        "dashboard_port": 5000,
        "dashboard_host": "0.0.0.0",
        "secret_key": "dev-secret-key-change-in-production",
        # Database
        "database_url": "sqlite:///data/bot.db",
        # Trading
        "paper_trading": True,
        "max_trade_size": 1000,
        "min_profit_margin": 0.02,
        # Monitoring
        "prometheus_port": 9090,
        "grafana_port": 3000,
        "redis_port": 6379,
        "sentry_dsn": "",
        "sentry_environment": "production",
        "sentry_traces_sample_rate": 0.1,
        # Security
        "jwt_secret_key": "change-this-jwt-secret-key",
        "jwt_expiration_hours": 24,
        "api_rate_limit": "100/hour",
        # Feature Flags
        "feature_real_trading": False,
        "feature_advanced_analytics": True,
        "feature_telegram_notifications": True,
        "feature_email_notifications": True,
        "feature_prometheus_metrics": True,
        # Performance
        "workers": 2,
        "worker_connections": 1000,
        "request_timeout": 30,
        # Rate Limiting
        "rate_limit_enabled": True,
        "rate_limit_default": "100/hour",
        "rate_limit_sensitive": "20/hour",
    }

    def __init__(
        self, config_path: Optional[str] = None, env_file: Optional[str] = None
    ):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to YAML configuration file
            env_file: Path to .env file (defaults to .env in project root)
        """
        self.config_path = config_path
        self.env_file = env_file or ".env"
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from all sources with proper precedence."""
        # Start with defaults
        self._config = self.DEFAULTS.copy()

        # Load from YAML file if specified
        if self.config_path:
            yaml_config = self._load_yaml()
            if yaml_config:
                self._merge_config(yaml_config)

        # Load environment variables (highest priority)
        self._load_env_file()
        self._load_env_vars()

        logger.info(
            f"Configuration loaded from: defaults, YAML: {bool(self.config_path)}, ENV: True"
        )

    def _load_yaml(self) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML file."""
        try:
            config_path = Path(self.config_path)
            if not config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return None

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded YAML config from: {self.config_path}")
                return config or {}
        except Exception as e:
            logger.error(f"Error loading YAML config: {e}")
            return None

    def _load_env_file(self):
        """Load environment variables from .env file."""
        try:
            env_path = Path(self.env_file)
            if env_path.exists():
                load_dotenv(env_path)
                logger.info(f"Loaded environment from: {self.env_file}")
            else:
                logger.debug(f".env file not found: {self.env_file}")
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")

    def _load_env_vars(self):
        """Load configuration from environment variables."""
        # Map environment variable names to config keys
        env_mappings = {
            "TRADING_BOT_ENV": "trading_bot_env",
            "DEBUG": "debug",
            "LOG_LEVEL": "log_level",
            "LOG_FORMAT": "log_format",
            "DASHBOARD_PORT": "dashboard_port",
            "DASHBOARD_HOST": "dashboard_host",
            "SECRET_KEY": "secret_key",
            "DATABASE_URL": "database_url",
            "PAPER_TRADING": "paper_trading",
            "MAX_TRADE_SIZE": "max_trade_size",
            "MIN_PROFIT_MARGIN": "min_profit_margin",
            "PROMETHEUS_PORT": "prometheus_port",
            "GRAFANA_PORT": "grafana_port",
            "REDIS_PORT": "redis_port",
            "SENTRY_DSN": "sentry_dsn",
            "SENTRY_ENVIRONMENT": "sentry_environment",
            "SENTRY_TRACES_SAMPLE_RATE": "sentry_traces_sample_rate",
            "JWT_SECRET_KEY": "jwt_secret_key",
            "JWT_EXPIRATION_HOURS": "jwt_expiration_hours",
            "API_RATE_LIMIT": "api_rate_limit",
            "FEATURE_REAL_TRADING": "feature_real_trading",
            "FEATURE_ADVANCED_ANALYTICS": "feature_advanced_analytics",
            "FEATURE_TELEGRAM_NOTIFICATIONS": "feature_telegram_notifications",
            "FEATURE_EMAIL_NOTIFICATIONS": "feature_email_notifications",
            "FEATURE_PROMETHEUS_METRICS": "feature_prometheus_metrics",
            "WORKERS": "workers",
            "WORKER_CONNECTIONS": "worker_connections",
            "REQUEST_TIMEOUT": "request_timeout",
            "RATE_LIMIT_ENABLED": "rate_limit_enabled",
            "RATE_LIMIT_DEFAULT": "rate_limit_default",
            "RATE_LIMIT_SENSITIVE": "rate_limit_sensitive",
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert value to appropriate type
                converted_value = self._convert_value(env_value, config_key)
                self._config[config_key] = converted_value
                logger.debug(f"Loaded from ENV: {config_key} = {converted_value}")

    def _convert_value(self, value: str, key: str) -> Any:
        """Convert string value to appropriate type based on key."""
        # Boolean conversion
        if key in ["debug", "paper_trading", "rate_limit_enabled"] or key.startswith(
            "feature_"
        ):
            return value.lower() in ["true", "1", "yes", "on"]

        # Integer conversion
        if key in [
            "dashboard_port",
            "prometheus_port",
            "grafana_port",
            "redis_port",
            "workers",
            "worker_connections",
            "request_timeout",
            "jwt_expiration_hours",
        ]:
            try:
                return int(value)
            except ValueError:
                logger.warning(
                    f"Could not convert {key}={value} to int, using as string"
                )
                return value

        # Float conversion
        if key in ["min_profit_margin", "sentry_traces_sample_rate"]:
            try:
                return float(value)
            except ValueError:
                logger.warning(
                    f"Could not convert {key}={value} to float, using as string"
                )
                return value

        # String (default)
        return value

    def _merge_config(self, new_config: Dict[str, Any], prefix: str = ""):
        """Recursively merge new configuration into existing config."""
        for key, value in new_config.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                # Recursively merge nested dicts
                self._merge_config(value, f"{full_key}_")
            else:
                self._config[full_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary of all configuration
        """
        return self._config.copy()

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.get("trading_bot_env", "").lower() == "production"

    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get("debug", False)

    def get_database_url(self) -> str:
        """Get database URL."""
        return self.get("database_url", self.DEFAULTS["database_url"])

    def get_secret_key(self) -> str:
        """Get Flask secret key."""
        secret = self.get("secret_key", self.DEFAULTS["secret_key"])
        if secret == self.DEFAULTS["secret_key"] and self.is_production():
            logger.warning(
                "Using default secret key in production! Please set SECRET_KEY environment variable."
            )
        return secret

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return {
            key.replace("feature_", ""): value
            for key, value in self._config.items()
            if key.startswith("feature_")
        }

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: Feature name (without 'feature_' prefix)

        Returns:
            True if feature is enabled, False otherwise
        """
        key = f"feature_{feature}"
        return self.get(key, False)


# Global instance (lazy loaded)
_config_loader: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None, reload: bool = False) -> ConfigLoader:
    """
    Get global configuration loader instance.

    Args:
        config_path: Path to YAML config file (used on first load).
            Defaults to CONFIG_PATH env var or "config.yaml".
        reload: Force reload configuration

    Returns:
        ConfigLoader instance
    """
    global _config_loader

    if _config_loader is None or reload:
        if config_path is None:
            config_path = os.environ.get("CONFIG_PATH", "config.yaml")
        _config_loader = ConfigLoader(config_path=config_path)

    return _config_loader
