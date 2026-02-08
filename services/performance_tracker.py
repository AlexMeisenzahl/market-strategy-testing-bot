"""
Real-Time Performance Tracking

Track and broadcast performance updates via WebSocket for real-time monitoring.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import json

from database.competition_models import (
    Strategy,
    StrategyPerformanceSnapshot
)
from logger import get_logger

logger = get_logger()


class RealTimePerformanceTracker:
    """Track and broadcast performance updates"""

    def __init__(self, socketio=None, max_history_hours: int = 24):
        """
        Initialize performance tracker
        
        Args:
            socketio: Flask-SocketIO instance for broadcasting
            max_history_hours: Hours of history to keep in memory
        """
        self.socketio = socketio
        self.max_history_hours = max_history_hours
        self.max_history_size = max_history_hours * 3600  # Assuming 1 second updates
        
        # In-memory storage for quick access (last 24 hours)
        self.performance_history = {}  # strategy_id -> deque of snapshots
        
        # Initialize history for all strategies
        self._initialize_history()

    def _initialize_history(self):
        """Initialize performance history from database"""
        try:
            strategies = Strategy.get_all()
            
            for strategy in strategies:
                strategy_id = strategy['id']
                
                # Get last 24 hours from database
                history = StrategyPerformanceSnapshot.get_history(
                    strategy_id, 
                    hours=self.max_history_hours
                )
                
                # Initialize deque with max size
                self.performance_history[strategy_id] = deque(
                    maxlen=self.max_history_size
                )
                
                # Load existing history
                for snapshot in history:
                    self.performance_history[strategy_id].append({
                        'timestamp': snapshot['timestamp'],
                        'portfolio_value': snapshot['portfolio_value'],
                        'return_pct': snapshot['total_return_pct'],
                        'pnl': snapshot['daily_pnl']
                    })
                
        except Exception as e:
            logger.error(f"Error initializing performance history: {e}")

    def take_snapshot(self, strategy_performance: Dict = None) -> Dict:
        """
        Take performance snapshot of all strategies
        
        Args:
            strategy_performance: Optional dict of strategy_id -> performance metrics
            
        Returns:
            Snapshot data
        """
        try:
            snapshot = {
                'timestamp': datetime.utcnow().isoformat(),
                'strategies': {}
            }
            
            strategies = Strategy.get_all()
            
            for strategy in strategies:
                strategy_id = strategy['id']
                strategy_name = strategy['name']
                
                # Get performance metrics
                if strategy_performance and strategy_id in strategy_performance:
                    metrics = strategy_performance[strategy_id]
                else:
                    # Get latest snapshot from database
                    db_snapshot = StrategyPerformanceSnapshot.get_latest(strategy_id)
                    if db_snapshot:
                        metrics = {
                            'portfolio_value': db_snapshot['portfolio_value'],
                            'return_pct': db_snapshot['total_return_pct'],
                            'daily_pnl': db_snapshot['daily_pnl'],
                            'sharpe_ratio': db_snapshot['sharpe_ratio'],
                            'total_trades': db_snapshot['total_trades'],
                            'win_rate': db_snapshot['win_rate'],
                            'open_positions': db_snapshot['open_positions']
                        }
                    else:
                        # Default values
                        metrics = {
                            'portfolio_value': 10000.0,
                            'return_pct': 0.0,
                            'daily_pnl': 0.0,
                            'sharpe_ratio': 0.0,
                            'total_trades': 0,
                            'win_rate': 0.0,
                            'open_positions': 0
                        }
                
                snapshot['strategies'][strategy_name] = metrics
                
                # Add to in-memory history
                if strategy_id not in self.performance_history:
                    self.performance_history[strategy_id] = deque(
                        maxlen=self.max_history_size
                    )
                
                self.performance_history[strategy_id].append({
                    'timestamp': int(datetime.utcnow().timestamp()),
                    'portfolio_value': metrics.get('portfolio_value', 10000.0),
                    'return_pct': metrics.get('return_pct', 0.0),
                    'pnl': metrics.get('daily_pnl', 0.0)
                })
            
            # Broadcast via WebSocket
            if self.socketio:
                self._broadcast_update(snapshot)
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error taking performance snapshot: {e}", exc_info=True)
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'strategies': {},
                'error': str(e)
            }

    def _broadcast_update(self, snapshot: Dict):
        """Broadcast snapshot via WebSocket"""
        try:
            if self.socketio:
                self.socketio.emit('performance_update', snapshot, namespace='/')
        except Exception as e:
            logger.error(f"Error broadcasting update: {e}")

    def get_historical_performance(
        self, 
        strategy_name: str, 
        hours: int = 24
    ) -> List[Dict]:
        """
        Get last X hours of performance data
        
        Args:
            strategy_name: Name of the strategy
            hours: Number of hours of history to return
            
        Returns:
            List of performance snapshots
        """
        try:
            # Get strategy ID
            strategy = Strategy.get_by_name(strategy_name)
            if not strategy:
                return []
            
            strategy_id = strategy['id']
            
            # Get from in-memory cache first
            if strategy_id in self.performance_history:
                history = list(self.performance_history[strategy_id])
                
                # Filter by time window
                cutoff_timestamp = int(datetime.utcnow().timestamp()) - (hours * 3600)
                filtered_history = [
                    h for h in history 
                    if h['timestamp'] >= cutoff_timestamp
                ]
                
                return filtered_history
            
            # Fallback to database
            db_history = StrategyPerformanceSnapshot.get_history(strategy_id, hours)
            return [
                {
                    'timestamp': s['timestamp'],
                    'portfolio_value': s['portfolio_value'],
                    'return_pct': s['total_return_pct'],
                    'pnl': s['daily_pnl']
                }
                for s in db_history
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical performance: {e}")
            return []

    def get_real_time_stats(self) -> Dict:
        """Get real-time statistics across all strategies"""
        try:
            strategies = Strategy.get_all()
            
            total_value = 0
            total_return = 0
            active_strategies = 0
            
            for strategy in strategies:
                if not strategy['enabled']:
                    continue
                
                active_strategies += 1
                strategy_id = strategy['id']
                
                # Get latest performance
                snapshot = StrategyPerformanceSnapshot.get_latest(strategy_id)
                if snapshot:
                    total_value += snapshot['portfolio_value'] or 0
                    total_return += snapshot['total_return_pct'] or 0
            
            avg_return = total_return / active_strategies if active_strategies > 0 else 0
            
            return {
                'total_value': round(total_value, 2),
                'avg_return': round(avg_return, 2),
                'active_strategies': active_strategies,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time stats: {e}")
            return {
                'total_value': 0,
                'avg_return': 0,
                'active_strategies': 0,
                'timestamp': datetime.utcnow().isoformat()
            }

    def save_hourly_snapshot(self):
        """Save hourly snapshot to database"""
        try:
            strategies = Strategy.get_all()
            
            for strategy in strategies:
                strategy_id = strategy['id']
                
                # Get latest in-memory performance
                if strategy_id in self.performance_history:
                    recent = list(self.performance_history[strategy_id])
                    if recent:
                        latest = recent[-1]
                        
                        # Save to database
                        StrategyPerformanceSnapshot.create(
                            strategy_id=strategy_id,
                            portfolio_value=latest['portfolio_value'],
                            total_return_pct=latest['return_pct'],
                            daily_pnl=latest['pnl'],
                            timestamp=latest['timestamp']
                        )
                        
                        logger.info(f"Saved hourly snapshot for strategy {strategy_id}")
            
        except Exception as e:
            logger.error(f"Error saving hourly snapshot: {e}", exc_info=True)


# Global instance (will be initialized with socketio in app)
performance_tracker = RealTimePerformanceTracker()
