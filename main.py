#!/usr/bin/env python3
"""
Canonical Entry Point - Market Strategy Testing Bot Engine

Starts the canonical execution engine (run_bot). This is the single
entry point for running the bot engine.

Usage:
    python main.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_bot import main as run_engine

if __name__ == "__main__":
    run_engine()
    sys.exit(0)
