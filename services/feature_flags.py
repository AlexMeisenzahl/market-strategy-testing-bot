"""
Feature Flags System for Trading Bot
Enables/disables features dynamically without code changes
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging


class FeatureFlags:
    """Feature flag management system"""
    
    # Default feature flags
    DEFAULT_FLAGS = {
        # Core features
        'real_trading': False,  # ALWAYS False for safety
        'paper_trading': True,
        
        # Monitoring & Observability
        'prometheus_metrics': True,
        'sentry_error_tracking': True,
        'advanced_analytics': True,
        
        # Notifications
        'telegram_notifications': True,
        'email_notifications': True,
        'discord_notifications': True,
        'slack_notifications': True,
        'webhook_notifications': True,
        
        # Trading strategies
        'arbitrage_strategy': True,
        'momentum_strategy': False,
        'mean_reversion_strategy': False,
        'reality_arbitrage_strategy': True,
        
        # API integrations
        'polymarket_api': True,
        'coingecko_api': True,
        'binance_api': True,
        'coinbase_api': False,
        
        # Performance features
        'caching': True,
        'request_pooling': True,
        'parallel_processing': False,
        
        # Security features
        'rate_limiting': True,
        'ip_whitelist': False,
        'jwt_authentication': True,
        'api_key_rotation': False,
        
        # Dashboard features
        'web_dashboard': True,
        'live_charts': True,
        'csv_export': True,
        'settings_import_export': True,
        
        # Experimental features
        'machine_learning': False,
        'backtesting': True,
        'portfolio_optimization': False,
        
        # Maintenance mode
        'maintenance_mode': False,
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.flags = self.DEFAULT_FLAGS.copy()
        self.config_path = config_path or 'config.yaml'
        
        # Load from environment variables first
        self._load_from_env()
        
        # Then load from config file (overrides env)
        if Path(self.config_path).exists():
            self._load_from_config()
        
        # Safety check: ensure real_trading is always False
        self.flags['real_trading'] = False
        
        self.logger.info(f"Feature flags initialized: {self._get_enabled_count()} enabled")
    
    def _load_from_env(self):
        """Load feature flags from environment variables"""
        for flag in self.flags.keys():
            env_var = f"FEATURE_{flag.upper()}"
            if env_var in os.environ:
                value = os.environ[env_var].lower() in ('true', '1', 'yes', 'on')
                self.flags[flag] = value
                self.logger.debug(f"Loaded {flag} from env: {value}")
    
    def _load_from_config(self):
        """Load feature flags from config file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'feature_flags' in config:
                for flag, value in config['feature_flags'].items():
                    if flag in self.flags:
                        self.flags[flag] = bool(value)
                        self.logger.debug(f"Loaded {flag} from config: {value}")
        except Exception as e:
            self.logger.error(f"Failed to load feature flags from config: {e}")
    
    def is_enabled(self, flag: str) -> bool:
        """Check if a feature flag is enabled"""
        # Safety check for real_trading
        if flag == 'real_trading':
            return False
        
        return self.flags.get(flag, False)
    
    def enable(self, flag: str):
        """Enable a feature flag (in memory only)"""
        # Prevent enabling real_trading
        if flag == 'real_trading':
            self.logger.warning("Cannot enable real_trading flag")
            return False
        
        if flag in self.flags:
            self.flags[flag] = True
            self.logger.info(f"Enabled feature flag: {flag}")
            return True
        
        self.logger.warning(f"Unknown feature flag: {flag}")
        return False
    
    def disable(self, flag: str):
        """Disable a feature flag (in memory only)"""
        if flag in self.flags:
            self.flags[flag] = False
            self.logger.info(f"Disabled feature flag: {flag}")
            return True
        
        self.logger.warning(f"Unknown feature flag: {flag}")
        return False
    
    def get_all(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.flags.copy()
    
    def get_enabled(self) -> Dict[str, bool]:
        """Get all enabled feature flags"""
        return {k: v for k, v in self.flags.items() if v}
    
    def get_disabled(self) -> Dict[str, bool]:
        """Get all disabled feature flags"""
        return {k: v for k, v in self.flags.items() if not v}
    
    def _get_enabled_count(self) -> int:
        """Get count of enabled flags"""
        return sum(1 for v in self.flags.values() if v)
    
    def save_to_config(self, config_path: Optional[str] = None) -> bool:
        """Save current flags to config file"""
        try:
            path = config_path or self.config_path
            
            # Load existing config
            config = {}
            if Path(path).exists():
                with open(path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            
            # Update feature_flags section
            config['feature_flags'] = self.flags
            
            # Write back
            with open(path, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False)
            
            self.logger.info(f"Feature flags saved to {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save feature flags: {e}")
            return False
    
    def is_maintenance_mode(self) -> bool:
        """Check if maintenance mode is enabled"""
        return self.is_enabled('maintenance_mode')
    
    def require_flag(self, flag: str):
        """Decorator to require a feature flag"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.is_enabled(flag):
                    raise FeatureFlagError(f"Feature '{flag}' is disabled")
                return func(*args, **kwargs)
            return wrapper
        return decorator


class FeatureFlagError(Exception):
    """Exception raised when a required feature is disabled"""
    pass


# Global instance
feature_flags = FeatureFlags()
