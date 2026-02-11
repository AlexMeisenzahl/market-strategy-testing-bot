"""
TUI monitor - read-only terminal interface.

Delegates to the existing bot.py implementation.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> None:
    """Run the TUI monitor."""
    from bot import main as _main
    _main()
