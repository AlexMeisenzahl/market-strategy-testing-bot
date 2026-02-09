"""
WebSocket Manager

Manages WebSocket connections for real-time updates.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from datetime import datetime
import json
import asyncio

from logger import get_logger

logger = get_logger()


class ConnectionManager:
    """
    Manages WebSocket connections
    
    Handles client connections and broadcasts real-time updates.
    """
    
    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: List[WebSocket] = []
        self.max_connections = 100
    
    async def connect(self, websocket: WebSocket):
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
        """
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Max connections reached")
            return
        
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.log_info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.log_info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send a message to a specific client
        
        Args:
            message: Message data
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.log_error(f"Failed to send personal message: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients
        
        Args:
            message: Message data
        """
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.log_error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_trade(self, trade_data: Dict[str, Any]):
        """
        Broadcast trade execution event
        
        Args:
            trade_data: Trade data
        """
        await self.broadcast({
            "type": "trade",
            "data": trade_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_position(self, position_data: Dict[str, Any]):
        """
        Broadcast position update event
        
        Args:
            position_data: Position data
        """
        await self.broadcast({
            "type": "position",
            "data": position_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_market_update(self, market_data: Dict[str, Any]):
        """
        Broadcast market price update event
        
        Args:
            market_data: Market data
        """
        await self.broadcast({
            "type": "market",
            "data": market_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_strategy_trigger(self, strategy_data: Dict[str, Any]):
        """
        Broadcast strategy trigger event
        
        Args:
            strategy_data: Strategy data
        """
        await self.broadcast({
            "type": "strategy",
            "data": strategy_data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def broadcast_status_change(self, status_data: Dict[str, Any]):
        """
        Broadcast bot status change event
        
        Args:
            status_data: Status data
        """
        await self.broadcast({
            "type": "status",
            "data": status_data,
            "timestamp": datetime.now().isoformat()
        })


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    
    Args:
        websocket: WebSocket connection
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connected to Polymarket Trading Bot",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong for keepalive
            if data == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            else:
                # Echo received message (for testing)
                await manager.send_personal_message({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.log_error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
