"""
Data Pipeline Monitor

Monitor WebSocket connection health and API response times.
"""

import logging
from typing import Dict
from datetime import datetime, timedelta
from collections import deque

from logger import get_logger

logger = get_logger()


class DataPipelineMonitor:
    """Monitor data pipeline health"""

    def __init__(
        self,
        websocket_timeout_seconds: int = 10,
        api_slow_threshold_ms: int = 2000,
        history_size: int = 100
    ):
        """
        Initialize data pipeline monitor
        
        Args:
            websocket_timeout_seconds: Timeout for WebSocket connection
            api_slow_threshold_ms: Threshold for slow API responses
            history_size: Number of recent checks to keep
        """
        self.websocket_timeout = websocket_timeout_seconds
        self.api_slow_threshold = api_slow_threshold_ms
        
        # Connection state
        self.websocket_connected = False
        self.last_websocket_message = None
        self.websocket_reconnect_count = 0
        
        # API monitoring
        self.api_response_times = deque(maxlen=history_size)
        self.api_error_count = 0
        self.last_api_check = None
        
        # Data freshness
        self.last_data_received = None

    def monitor_websocket(self) -> Dict:
        """Monitor WebSocket connection health"""
        try:
            now = datetime.utcnow()
            
            # Check if we've received data recently
            if self.last_websocket_message:
                time_since_message = (now - self.last_websocket_message).total_seconds()
                
                if time_since_message > self.websocket_timeout:
                    status = 'down'
                    message = f"No data for {time_since_message:.1f}s (timeout: {self.websocket_timeout}s)"
                elif time_since_message > self.websocket_timeout / 2:
                    status = 'degraded'
                    message = f"Slow updates ({time_since_message:.1f}s since last message)"
                else:
                    status = 'healthy'
                    message = 'Receiving data'
            else:
                status = 'unknown'
                message = 'No data received yet'
            
            return {
                'status': status,
                'message': message,
                'connected': self.websocket_connected,
                'last_message': self.last_websocket_message.isoformat() if self.last_websocket_message else None,
                'reconnect_count': self.websocket_reconnect_count,
                'timestamp': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring WebSocket: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def monitor_api_health(self) -> Dict:
        """Monitor API response times"""
        try:
            if not self.api_response_times:
                return {
                    'status': 'unknown',
                    'message': 'No API calls yet',
                    'avg_response_time_ms': 0
                }
            
            # Calculate average response time
            avg_response_time = sum(self.api_response_times) / len(self.api_response_times)
            
            # Determine status
            if avg_response_time > self.api_slow_threshold:
                status = 'degraded'
                message = f"Slow API responses ({avg_response_time:.0f}ms avg)"
            elif self.api_error_count > 5:
                status = 'degraded'
                message = f"High error count ({self.api_error_count} errors)"
            else:
                status = 'healthy'
                message = 'API responding normally'
            
            return {
                'status': status,
                'message': message,
                'avg_response_time_ms': round(avg_response_time, 0),
                'error_count': self.api_error_count,
                'recent_calls': len(self.api_response_times),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring API health: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def record_websocket_message(self):
        """Record that a WebSocket message was received"""
        self.last_websocket_message = datetime.utcnow()
        self.last_data_received = datetime.utcnow()
        self.websocket_connected = True

    def record_websocket_disconnect(self):
        """Record WebSocket disconnection"""
        self.websocket_connected = False
        self.websocket_reconnect_count += 1
        logger.warning(f"WebSocket disconnected (reconnect #{self.websocket_reconnect_count})")

    def record_api_call(self, response_time_ms: float, success: bool = True):
        """
        Record an API call
        
        Args:
            response_time_ms: Response time in milliseconds
            success: Whether the call succeeded
        """
        self.api_response_times.append(response_time_ms)
        self.last_api_check = datetime.utcnow()
        
        if not success:
            self.api_error_count += 1

    def check_data_freshness(self) -> str:
        """
        Check if data is fresh
        
        Returns:
            Status: 'fresh' or 'stale'
        """
        if not self.last_data_received:
            return 'unknown'
        
        age_seconds = (datetime.utcnow() - self.last_data_received).total_seconds()
        
        if age_seconds > 10:
            return 'stale'
        elif age_seconds > 5:
            return 'aging'
        else:
            return 'fresh'

    def get_health_status(self) -> Dict:
        """
        Get overall data pipeline health
        
        Returns:
            Overall health status
        """
        try:
            websocket_health = self.monitor_websocket()
            api_health = self.monitor_api_health()
            data_freshness = self.check_data_freshness()
            
            # Determine overall status
            statuses = [websocket_health['status'], api_health['status']]
            
            if 'down' in statuses or 'error' in statuses:
                overall = 'critical'
            elif 'degraded' in statuses or data_freshness == 'stale':
                overall = 'degraded'
            elif 'unknown' in statuses:
                overall = 'unknown'
            else:
                overall = 'healthy'
            
            return {
                'overall': overall,
                'websocket': websocket_health['status'],
                'api': api_health['status'],
                'data_freshness': data_freshness,
                'details': {
                    'websocket': websocket_health,
                    'api': api_health
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}", exc_info=True)
            return {
                'overall': 'error',
                'websocket': 'error',
                'api': 'error',
                'data_freshness': 'unknown',
                'error': str(e)
            }

    def auto_reconnect_websocket(self) -> bool:
        """
        Auto-reconnect WebSocket if disconnected
        
        Returns:
            True if reconnection attempted, False otherwise
        """
        try:
            if not self.websocket_connected:
                logger.info("Attempting WebSocket reconnection...")
                # TODO: Integrate with actual WebSocket reconnection logic
                return True
            return False
        except Exception as e:
            logger.error(f"Error auto-reconnecting WebSocket: {e}")
            return False


# Global instance
data_monitor = DataPipelineMonitor()
