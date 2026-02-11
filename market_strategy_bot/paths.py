"""
Environment-configurable paths for the Market Strategy Bot.

All paths can be overridden via environment variables:
- STATE_DIR: Directory for bot_state.json, control.json (default: state)
- LOG_DIR: Directory for logs (default: logs)
- CONFIG_PATH: Path to config file (default: config.yaml)

Paths are resolved relative to PROJECT_ROOT unless an absolute path is provided.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(env_var: str, default: str, base: Path = PROJECT_ROOT) -> Path:
    """Resolve path from env or default; return absolute path."""
    value = os.environ.get(env_var, default)
    p = Path(value)
    if not p.is_absolute():
        p = base / p
    return p


def get_state_dir() -> Path:
    """State directory: bot_state.json, control.json."""
    return _resolve_path("STATE_DIR", "state")


def get_log_dir() -> Path:
    """Log directory: activity.json, trades.csv, errors.log, etc."""
    return _resolve_path("LOG_DIR", "logs")


def get_config_path() -> Path:
    """Config file path (YAML)."""
    return _resolve_path("CONFIG_PATH", "config.yaml")


# Note: Use get_state_dir(), get_log_dir(), get_config_path() at runtime
# so environment variable changes are picked up.
