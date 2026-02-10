"""
WebSocket Server - Real-Time Dashboard Updates

Provides WebSocket support for real-time data streaming to the dashboard.
"""

from flask_socketio import SocketIO, emit
from threading import Thread
import time
from typing import Dict, Any

from logger import get_logger

# Initialize SocketIO (will be configured in app.py)
socketio = None

# Global data cache for broadcasting
live_data = {
    "portfolio": {},
    "trades": [],
    "strategies": {},
    "alerts": []
}

# Background broadcast thread
broadcast_thread = None
broadcast_active = False


def init_socketio(app):
    """
    Initialize SocketIO with Flask app
    
    Args:
        app: Flask application instance
    """
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Setup event handlers
    setup_event_handlers()
    
    # Start background broadcast thread
    start_broadcast_thread()
    
    logger = get_logger()
    logger.log_info("WebSocket server initialized")
    
    return socketio


def setup_event_handlers():
    """Setup WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger = get_logger()
        logger.log_info("WebSocket client connected")
        
        # Send initial data to newly connected client
        emit('initial_data', live_data)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger = get_logger()
        logger.log_info("WebSocket client disconnected")
    
    @socketio.on('request_update')
    def handle_request_update():
        """Handle manual update request"""
        emit('portfolio_update', live_data['portfolio'])
        emit('trades_update', live_data['trades'][-10:])
        emit('strategies_update', live_data['strategies'])
        emit('alerts_update', live_data['alerts'])


def broadcast_updates():
    """Background thread to broadcast updates periodically"""
    global broadcast_active
    logger = get_logger()
    
    while broadcast_active:
        try:
            if socketio:
                # Emit portfolio updates
                socketio.emit('portfolio_update', live_data['portfolio'])
                
                # Emit recent trades (last 10)
                socketio.emit('trades_update', live_data['trades'][-10:])
                
                # Emit strategy status
                socketio.emit('strategies_update', live_data['strategies'])
                
                # Emit alerts
                if live_data['alerts']:
                    socketio.emit('alerts_update', live_data['alerts'])
            
            # Wait 5 seconds before next broadcast
            time.sleep(5)
            
        except Exception as e:
            logger.log_error(f"Error in broadcast thread: {e}")
            time.sleep(5)  # Wait before retrying


def start_broadcast_thread():
    """Start the background broadcast thread"""
    global broadcast_thread, broadcast_active
    
    if broadcast_thread is None or not broadcast_thread.is_alive():
        broadcast_active = True
        broadcast_thread = Thread(target=broadcast_updates, daemon=True)
        broadcast_thread.start()
        
        logger = get_logger()
        logger.log_info("WebSocket broadcast thread started")


def stop_broadcast_thread():
    """Stop the background broadcast thread"""
    global broadcast_active
    broadcast_active = False
    
    logger = get_logger()
    logger.log_info("WebSocket broadcast thread stopped")


def update_live_data(data_type: str, data: Any):
    """
    Update live data cache
    
    Args:
        data_type: Type of data ('portfolio', 'trades', 'strategies', 'alerts')
        data: Data to update
    """
    global live_data
    
    if data_type in live_data:
        if data_type == 'trades':
            # Append to trades list and keep last 100
            if isinstance(data, list):
                live_data['trades'].extend(data)
            else:
                live_data['trades'].append(data)
            live_data['trades'] = live_data['trades'][-100:]
        else:
            live_data[data_type] = data
