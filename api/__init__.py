"""
Mobile Backend API Module

FastAPI-based REST API and WebSocket server for mobile trading bot control.
"""

from .server import app, run_server, set_bot_instance, get_bot, get_config

__all__ = ["app", "run_server", "set_bot_instance", "get_bot", "get_config"]
