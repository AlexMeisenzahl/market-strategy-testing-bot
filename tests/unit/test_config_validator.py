"""
Unit Tests for Config Validator

Tests the configuration validation system.
"""

import pytest
import yaml
from pathlib import Path
from utils.config_validator import ConfigValidator


class TestConfigValidator:
    """Tests for ConfigValidator class."""

    def test_valid_config(self, tmp_path):
        """Test validation of a valid configuration."""
        config_file = tmp_path / "config.yaml"
        config = {
            "paper_trading": True,
            "kill_switch": False,
            "data_sources": {
                "crypto_prices": {"primary": "binance", "fallback": "coingecko"},
                "polymarket": {"method": "subgraph", "cache_ttl_seconds": 60},
            },
            "polymarket": {
                "api": {"enabled": False, "rate_limit": 60, "timeout": 10},
                "market_filters": {"min_liquidity": 1000, "min_volume_24h": 5000},
            },
            "max_trade_size": 10,
            "min_profit_margin": 0.02,
            "max_trades_per_hour": 5,
            "max_trades_per_day": 50,
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        validator = ConfigValidator(str(config_file))
        is_valid, errors, warnings = validator.validate()

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_section(self, tmp_path):
        """Test detection of missing required sections."""
        config_file = tmp_path / "config.yaml"
        config = {
            "paper_trading": True
            # Missing data_sources and polymarket
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        validator = ConfigValidator(str(config_file))
        is_valid, errors, warnings = validator.validate()

        assert is_valid is False
        assert any("data_sources" in e for e in errors)
        assert any("polymarket" in e for e in errors)

    def test_invalid_crypto_source(self, tmp_path):
        """Test detection of invalid crypto data source."""
        config_file = tmp_path / "config.yaml"
        config = {
            "paper_trading": True,
            "data_sources": {"crypto_prices": {"primary": "invalid_source"}},
            "polymarket": {},
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        validator = ConfigValidator(str(config_file))
        is_valid, errors, warnings = validator.validate()

        assert is_valid is False
        assert any("Invalid primary crypto source" in e for e in errors)

    def test_invalid_trading_parameters(self, tmp_path):
        """Test detection of invalid trading parameters."""
        config_file = tmp_path / "config.yaml"
        config = {
            "paper_trading": True,
            "data_sources": {},
            "polymarket": {},
            "max_trade_size": -10,  # Invalid: negative
            "min_profit_margin": 1.5,  # Invalid: > 1
            "max_trades_per_hour": 0,  # Invalid: must be positive
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        validator = ConfigValidator(str(config_file))
        is_valid, errors, warnings = validator.validate()

        assert is_valid is False
        assert any("max_trade_size" in e for e in errors)
        assert any("min_profit_margin" in e for e in errors)
        assert any("max_trades_per_hour" in e for e in errors)

    def test_warning_for_live_trading(self, tmp_path):
        """Test warning generation for live trading mode."""
        config_file = tmp_path / "config.yaml"
        config = {
            "paper_trading": False,  # Should generate warning
            "data_sources": {},
            "polymarket": {},
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        validator = ConfigValidator(str(config_file))
        is_valid, errors, warnings = validator.validate()

        assert any("real money" in w.lower() for w in warnings)

    def test_kill_switch_warning(self, tmp_path):
        """Test warning generation for active kill switch."""
        config_file = tmp_path / "config.yaml"
        config = {
            "paper_trading": True,
            "kill_switch": True,  # Should generate warning
            "data_sources": {},
            "polymarket": {},
        }

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        validator = ConfigValidator(str(config_file))
        is_valid, errors, warnings = validator.validate()

        assert any("Kill switch" in w for w in warnings)

    def test_file_not_found(self):
        """Test handling of non-existent config file."""
        validator = ConfigValidator("nonexistent.yaml")
        is_valid, errors, warnings = validator.validate()

        assert is_valid is False
        assert any("not found" in e.lower() for e in errors)

    def test_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML syntax."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            f.write("invalid: yaml: syntax:\n  - bad\n  bad")

        validator = ConfigValidator(str(config_file))
        is_valid, errors, warnings = validator.validate()

        assert is_valid is False
        assert any("YAML" in e for e in errors)
