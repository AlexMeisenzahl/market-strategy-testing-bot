"""
Real-Time WebSocket Server

Provides real-time push updates to dashboard clients using WebSockets.
Replaces 30-second polling with instant push notifications for:
- Price updates
- Trade executions
- Strategy signals
- Portfolio changes
- Market opportunities
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import json
from threading import Thread, Lock
import time

from logger import get_logger


class RealtimeServer:
    """
    WebSocket server for real-time dashboard updates

    Features:
    - Sub-second latency push updates
    - Room-based event broadcasting
    - Connection management
    - Event queuing and throttling
    - Automatic reconnection handling
    """

    def __init__(self, flask_app: Flask, logger=None):
        """
        Initialize realtime server

        Args:
            flask_app: Flask application instance
            logger: Logger instance
        """
        self.app = flask_app
        self.logger = logger or get_logger()

        # Initialize SocketIO with CORS support
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode="threading",
            logger=False,
            engineio_logger=False,
        )

        # Connection tracking
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.connection_lock = Lock()

        # Event queues for different rooms
        self.event_queues: Dict[str, List[Dict]] = {
            "prices": [],
            "trades": [],
            "signals": [],
            "portfolio": [],
            "opportunities": [],
            "system": [],
        }
        self.queue_lock = Lock()

        # Rate limiting
        self.last_broadcast_time: Dict[str, float] = {}
        self.min_broadcast_interval = 0.1  # 100ms minimum between broadcasts

        # Register socket event handlers
        self._register_handlers()

        # Statistics
        self.stats = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_queued": 0,
            "start_time": datetime.now(),
        }

    def _register_handlers(self):
        """Register WebSocket event handlers"""

        @self.socketio.on("connect")
        def handle_connect():
            """Handle client connection"""
            client_id = self._get_client_id()

            with self.connection_lock:
                self.active_connections[client_id] = {
                    "connected_at": datetime.now(),
                    "rooms": ["system"],
                }
                self.stats["total_connections"] += 1

            # Join system room by default
            join_room("system")

            # Send welcome message
            emit(
                "connected",
                {
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                    "server_time": time.time(),
                },
            )

            if self.logger:
                self.logger.log_event(f"WebSocket client connected: {client_id}")

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """Handle client disconnection"""
            client_id = self._get_client_id()

            with self.connection_lock:
                if client_id in self.active_connections:
                    del self.active_connections[client_id]

            if self.logger:
                self.logger.log_event(f"WebSocket client disconnected: {client_id}")

        @self.socketio.on("subscribe")
        def handle_subscribe(data):
            """Handle room subscription"""
            room = data.get("room", "system")
            client_id = self._get_client_id()

            join_room(room)

            with self.connection_lock:
                if client_id in self.active_connections:
                    if "rooms" not in self.active_connections[client_id]:
                        self.active_connections[client_id]["rooms"] = []
                    if room not in self.active_connections[client_id]["rooms"]:
                        self.active_connections[client_id]["rooms"].append(room)

            emit(
                "subscribed",
                {
                    "room": room,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.socketio.on("unsubscribe")
        def handle_unsubscribe(data):
            """Handle room unsubscription"""
            room = data.get("room")
            client_id = self._get_client_id()

            leave_room(room)

            with self.connection_lock:
                if client_id in self.active_connections:
                    rooms = self.active_connections[client_id].get("rooms", [])
                    if room in rooms:
                        rooms.remove(room)

            emit(
                "unsubscribed",
                {
                    "room": room,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.socketio.on("ping")
        def handle_ping():
            """Handle ping for connection keepalive"""
            emit(
                "pong",
                {
                    "timestamp": datetime.now().isoformat(),
                    "server_time": time.time(),
                },
            )

    def broadcast_price_update(
        self, symbol: str, price: float, change_pct: float = None, volume: float = None
    ) -> None:
        """
        Broadcast price update to subscribed clients

        Args:
            symbol: Trading symbol
            price: Current price
            change_pct: Price change percentage
            volume: Trading volume
        """
        event_data = {
            "symbol": symbol,
            "price": price,
            "change_pct": change_pct,
            "volume": volume,
            "timestamp": datetime.now().isoformat(),
        }

        self._broadcast_to_room("prices", "price_update", event_data)

    def broadcast_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        profit: float = None,
        strategy: str = None,
    ) -> None:
        """
        Broadcast trade execution to subscribed clients

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Trade quantity
            price: Execution price
            profit: Realized profit (if closing position)
            strategy: Strategy name
        """
        event_data = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "profit": profit,
            "strategy": strategy,
            "timestamp": datetime.now().isoformat(),
        }

        self._broadcast_to_room("trades", "trade_executed", event_data)

    def broadcast_signal(
        self,
        symbol: str,
        strategy: str,
        signal_type: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Broadcast strategy signal to subscribed clients

        Args:
            symbol: Trading symbol
            strategy: Strategy name
            signal_type: Type of signal (e.g., 'bullish', 'bearish', 'arbitrage')
            details: Signal details
        """
        event_data = {
            "symbol": symbol,
            "strategy": strategy,
            "signal_type": signal_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        self._broadcast_to_room("signals", "signal_detected", event_data)

    def broadcast_opportunity(
        self,
        market_id: str,
        market_name: str,
        opportunity_type: str,
        profit_margin: float,
        details: Dict[str, Any],
    ) -> None:
        """
        Broadcast arbitrage opportunity to subscribed clients

        Args:
            market_id: Market identifier
            market_name: Market name
            opportunity_type: Type of opportunity
            profit_margin: Expected profit margin
            details: Opportunity details
        """
        event_data = {
            "market_id": market_id,
            "market_name": market_name,
            "opportunity_type": opportunity_type,
            "profit_margin": profit_margin,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        self._broadcast_to_room("opportunities", "opportunity_found", event_data)

    def broadcast_portfolio_update(
        self,
        cash_balance: float,
        portfolio_value: float,
        total_return: float,
        positions: List[Dict],
    ) -> None:
        """
        Broadcast portfolio update to subscribed clients

        Args:
            cash_balance: Current cash balance
            portfolio_value: Total portfolio value
            total_return: Total return percentage
            positions: List of open positions
        """
        event_data = {
            "cash_balance": cash_balance,
            "portfolio_value": portfolio_value,
            "total_return": total_return,
            "positions": positions,
            "timestamp": datetime.now().isoformat(),
        }

        self._broadcast_to_room("portfolio", "portfolio_updated", event_data)

    def broadcast_system_message(
        self, message: str, level: str = "info", details: Dict = None
    ) -> None:
        """
        Broadcast system message to all clients

        Args:
            message: Message text
            level: Message level ('info', 'warning', 'error', 'success')
            details: Additional details
        """
        event_data = {
            "message": message,
            "level": level,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }

        self._broadcast_to_room("system", "system_message", event_data)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        with self.connection_lock:
            active_count = len(self.active_connections)

        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "active_connections": active_count,
            "total_connections": self.stats["total_connections"],
            "messages_sent": self.stats["messages_sent"],
            "messages_queued": self.stats["messages_queued"],
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
        }

    def run(self, host: str = "0.0.0.0", port: int = 5001, debug: bool = False):
        """
        Run the WebSocket server

        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        if self.logger:
            self.logger.log_event(f"Starting WebSocket server on {host}:{port}")

        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True,  # For development
        )

    # Private helper methods

    def _get_client_id(self) -> str:
        """Get current client session ID"""
        from flask import request

        return request.sid

    def _broadcast_to_room(
        self, room: str, event_name: str, data: Dict[str, Any]
    ) -> None:
        """
        Broadcast event to a specific room with rate limiting

        Args:
            room: Room name
            event_name: Event name
            data: Event data
        """
        # Check rate limiting
        current_time = time.time()
        last_time = self.last_broadcast_time.get(f"{room}:{event_name}", 0)

        if current_time - last_time < self.min_broadcast_interval:
            # Queue the event instead of sending immediately
            with self.queue_lock:
                self.event_queues[room].append(
                    {
                        "event": event_name,
                        "data": data,
                        "queued_at": current_time,
                    }
                )
                self.stats["messages_queued"] += 1
            return

        # Broadcast immediately
        self.socketio.emit(event_name, data, room=room)
        self.last_broadcast_time[f"{room}:{event_name}"] = current_time
        self.stats["messages_sent"] += 1

    def _process_queued_events(self):
        """Process queued events (called periodically)"""
        with self.queue_lock:
            for room, queue in self.event_queues.items():
                if queue:
                    # Process oldest event in queue
                    event = queue.pop(0)
                    self.socketio.emit(
                        event["event"],
                        event["data"],
                        room=room,
                    )
                    self.stats["messages_sent"] += 1


# Global instance (will be initialized in dashboard app)
realtime_server: Optional[RealtimeServer] = None


def init_realtime_server(flask_app: Flask, logger=None) -> RealtimeServer:
    """
    Initialize the global realtime server instance

    Args:
        flask_app: Flask application instance
        logger: Logger instance

    Returns:
        RealtimeServer instance
    """
    global realtime_server
    realtime_server = RealtimeServer(flask_app, logger)
    return realtime_server


def get_realtime_server() -> Optional[RealtimeServer]:
    """Get the global realtime server instance"""
    return realtime_server
