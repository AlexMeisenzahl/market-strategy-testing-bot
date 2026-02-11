"""
Bot runner - delegates to the canonical run_bot implementation.

Ensures project root is on sys.path before importing.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def main(config_path: str = None) -> None:
    """Run the trading engine."""
    from run_bot import main as _main
    # run_bot.main() uses config_path internally via BotRunner
    _main()
