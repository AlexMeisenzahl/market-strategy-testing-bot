"""
Configuration Validation System

Validates config.yaml structure and values to catch configuration errors early.
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


class ConfigValidator:
    """Validates configuration files for completeness and correctness."""
    
    # Required top-level sections
    REQUIRED_SECTIONS = ['paper_trading', 'data_sources', 'polymarket']
    
    # Valid trading modes
    VALID_TRADING_MODES = ['paper', 'live']
    
    # Valid crypto price sources
    VALID_CRYPTO_SOURCES = ['binance', 'coingecko', 'coinbase']
    
    # Valid polymarket methods
    VALID_POLYMARKET_METHODS = ['subgraph', 'api']
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize validator.
        
        Args:
            config_path: Path to config file
        """
        self.config_path = Path(config_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.config: Optional[Dict[str, Any]] = None
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate configuration file.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Check file exists
        if not self.config_path.exists():
            self.errors.append(f"Config file not found: {self.config_path}")
            return False, self.errors, self.warnings
        
        # Load config
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax: {e}")
            return False, self.errors, self.warnings
        except Exception as e:
            self.errors.append(f"Error loading config: {e}")
            return False, self.errors, self.warnings
        
        if not isinstance(self.config, dict):
            self.errors.append("Config must be a dictionary")
            return False, self.errors, self.warnings
        
        # Validate sections
        self._validate_required_sections()
        self._validate_safety_settings()
        self._validate_data_sources()
        self._validate_polymarket_config()
        self._validate_trading_parameters()
        self._validate_notification_settings()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_required_sections(self):
        """Validate that required sections exist."""
        for section in self.REQUIRED_SECTIONS:
            if section not in self.config:
                self.errors.append(f"Missing required section: '{section}'")
    
    def _validate_safety_settings(self):
        """Validate safety-critical settings."""
        # Paper trading check
        if 'paper_trading' in self.config:
            if not isinstance(self.config['paper_trading'], bool):
                self.errors.append("'paper_trading' must be a boolean")
            elif self.config['paper_trading'] is False:
                self.warnings.append("WARNING: paper_trading is FALSE - real money mode!")
        
        # Kill switch check
        if 'kill_switch' in self.config:
            if not isinstance(self.config['kill_switch'], bool):
                self.errors.append("'kill_switch' must be a boolean")
            elif self.config['kill_switch'] is True:
                self.warnings.append("Kill switch is ACTIVE - bot will not trade")
    
    def _validate_data_sources(self):
        """Validate data sources configuration."""
        if 'data_sources' not in self.config:
            return
        
        data_sources = self.config['data_sources']
        
        # Crypto prices
        if 'crypto_prices' in data_sources:
            crypto = data_sources['crypto_prices']
            
            if 'primary' in crypto:
                if crypto['primary'] not in self.VALID_CRYPTO_SOURCES:
                    self.errors.append(
                        f"Invalid primary crypto source: {crypto['primary']}. "
                        f"Valid options: {', '.join(self.VALID_CRYPTO_SOURCES)}"
                    )
            
            if 'fallback' in crypto:
                if crypto['fallback'] not in self.VALID_CRYPTO_SOURCES:
                    self.errors.append(
                        f"Invalid fallback crypto source: {crypto['fallback']}. "
                        f"Valid options: {', '.join(self.VALID_CRYPTO_SOURCES)}"
                    )
        
        # Polymarket
        if 'polymarket' in data_sources:
            poly = data_sources['polymarket']
            
            if 'method' in poly:
                if poly['method'] not in self.VALID_POLYMARKET_METHODS:
                    self.errors.append(
                        f"Invalid polymarket method: {poly['method']}. "
                        f"Valid options: {', '.join(self.VALID_POLYMARKET_METHODS)}"
                    )
            
            if 'cache_ttl_seconds' in poly:
                ttl = poly['cache_ttl_seconds']
                if not isinstance(ttl, (int, float)) or ttl < 0:
                    self.errors.append("cache_ttl_seconds must be a positive number")
    
    def _validate_polymarket_config(self):
        """Validate Polymarket API configuration."""
        if 'polymarket' not in self.config:
            return
        
        polymarket = self.config['polymarket']
        
        # API settings
        if 'api' in polymarket:
            api = polymarket['api']
            
            if 'enabled' in api and not isinstance(api['enabled'], bool):
                self.errors.append("polymarket.api.enabled must be a boolean")
            
            if 'rate_limit' in api:
                rate = api['rate_limit']
                if not isinstance(rate, (int, float)) or rate <= 0:
                    self.errors.append("polymarket.api.rate_limit must be positive")
            
            if 'timeout' in api:
                timeout = api['timeout']
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    self.errors.append("polymarket.api.timeout must be positive")
        
        # Market filters
        if 'market_filters' in polymarket:
            filters = polymarket['market_filters']
            
            if 'min_liquidity' in filters:
                liq = filters['min_liquidity']
                if not isinstance(liq, (int, float)) or liq < 0:
                    self.errors.append("min_liquidity must be non-negative")
            
            if 'min_volume_24h' in filters:
                vol = filters['min_volume_24h']
                if not isinstance(vol, (int, float)) or vol < 0:
                    self.errors.append("min_volume_24h must be non-negative")
    
    def _validate_trading_parameters(self):
        """Validate trading parameter limits."""
        # Max trade size
        if 'max_trade_size' in self.config:
            size = self.config['max_trade_size']
            if not isinstance(size, (int, float)) or size <= 0:
                self.errors.append("max_trade_size must be positive")
            elif size > 1000:
                self.warnings.append(
                    f"max_trade_size is ${size} - consider lowering for safety"
                )
        
        # Min profit margin
        if 'min_profit_margin' in self.config:
            margin = self.config['min_profit_margin']
            if not isinstance(margin, (int, float)) or margin < 0 or margin > 1:
                self.errors.append("min_profit_margin must be between 0 and 1")
            elif margin < 0.01:
                self.warnings.append(
                    f"min_profit_margin is {margin*100}% - very low threshold"
                )
        
        # Rate limits
        if 'max_trades_per_hour' in self.config:
            rate = self.config['max_trades_per_hour']
            if not isinstance(rate, int) or rate <= 0:
                self.errors.append("max_trades_per_hour must be a positive integer")
        
        if 'max_trades_per_day' in self.config:
            daily = self.config['max_trades_per_day']
            if not isinstance(daily, int) or daily <= 0:
                self.errors.append("max_trades_per_day must be a positive integer")
    
    def _validate_notification_settings(self):
        """Validate notification configuration."""
        if 'notifications' not in self.config:
            return
        
        notif = self.config['notifications']
        
        # Quiet hours
        if 'quiet_hours_start' in notif:
            start = notif['quiet_hours_start']
            if not isinstance(start, int) or start < 0 or start > 23:
                self.errors.append("quiet_hours_start must be 0-23")
        
        if 'quiet_hours_end' in notif:
            end = notif['quiet_hours_end']
            if not isinstance(end, int) or end < 0 or end > 23:
                self.errors.append("quiet_hours_end must be 0-23")
        
        # Email settings
        if 'email' in notif:
            email = notif['email']
            
            if 'smtp_server' in email and not email['smtp_server']:
                self.warnings.append("email.smtp_server is empty")
            
            if 'smtp_port' in email:
                port = email['smtp_port']
                if not isinstance(port, int) or port <= 0 or port > 65535:
                    self.errors.append("smtp_port must be 1-65535")
        
        # Telegram settings
        if 'telegram' in notif:
            telegram = notif['telegram']
            
            if 'bot_token' in telegram and not telegram['bot_token']:
                self.warnings.append("telegram.bot_token is empty")


def main():
    """
    CLI tool to validate configuration.
    
    Usage:
        python -m utils.config_validator
        python -m utils.config_validator path/to/config.yaml
    """
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    
    validator = ConfigValidator(config_file)
    is_valid, errors, warnings = validator.validate()
    
    print(f"\n🔍 Validating: {config_file}\n")
    
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  • {error}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
        print()
    
    if is_valid:
        print("✅ Configuration is valid!\n")
        return 0
    else:
        print("❌ Configuration has errors - please fix them.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
