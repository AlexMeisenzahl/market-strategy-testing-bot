"""
Data Flow Manager - Orchestrates Data Flow

Manages the flow of data from strategies → trades → dashboard.
Coordinates between portfolio tracking, trade logging, and dashboard updates.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from logger import get_logger
from services.portfolio_tracker import PortfolioTracker
from services.trade_logger import TradeLogger
from services.paper_trading_engine import PaperTradingEngine


class DataFlowManager:
    """Manages data flow from strategies → trades → dashboard"""
    
    _instance = None  # Singleton instance
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data flow manager
        
        Args:
            config: Configuration dictionary
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
            
        self.logger = get_logger()
        self.config = config or {}
        
        # Initialize components
        initial_balance = self.config.get('initial_capital', 10000.0)
        self.portfolio_tracker = PortfolioTracker(initial_balance=initial_balance)
        self.trade_logger = TradeLogger()
        self.paper_trading_engine = PaperTradingEngine(self.config)
        
        # Dashboard cache for WebSocket broadcasting
        self.dashboard_cache = {
            'portfolio': {},
            'trades': [],
            'strategies': {},
            'alerts': []
        }
        
        self._initialized = True
        self.logger.log_info("DataFlowManager initialized")
    
    def process_signal(self, strategy_name: str, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process trading signal from strategy
        
        Args:
            strategy_name: Name of strategy generating signal
            signal: Signal dictionary with action, symbol, etc.
            
        Returns:
            Trade dictionary if executed, None otherwise
        """
        try:
            # 1. Execute trade via paper trading engine
            trade = self.execute_signal(signal)
            
            if not trade:
                return None
            
            # Add strategy name to trade
            trade['strategy'] = strategy_name
            
            # 2. Update portfolio
            self.portfolio_tracker.update(trade)
            
            # 3. Log trade
            self.trade_logger.log(trade)
            
            # 4. Update dashboard cache
            self.update_dashboard_cache(strategy_name, trade)
            
            # 5. Broadcast via WebSocket (if available)
            self._broadcast_update(trade)
            
            self.logger.log_info(
                f"Processed signal from {strategy_name}: {trade.get('side')} "
                f"{trade.get('quantity')} {trade.get('symbol')}"
            )
            
            return trade
            
        except Exception as e:
            self.logger.log_error(f"Error processing signal from {strategy_name}: {e}")
            return None
    
    def execute_signal(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute trade based on signal
        
        Args:
            signal: Signal dictionary
            
        Returns:
            Trade dictionary if successful
        """
        try:
            # Extract signal details
            action = signal.get('action', '').upper()
            symbol = signal.get('symbol', signal.get('market_id', ''))
            price = signal.get('price', 0)
            quantity = signal.get('quantity', signal.get('size', 0))
            
            if not symbol or not price or not quantity:
                self.logger.log_warning(f"Invalid signal: {signal}")
                return None
            
            # Create trade
            trade = {
                'symbol': symbol,
                'side': action,
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'filled',
                'pnl': 0  # Will be calculated on position close
            }
            
            return trade
            
        except Exception as e:
            self.logger.log_error(f"Error executing signal: {e}")
            return None
    
    def update_dashboard_cache(self, strategy_name: str, trade: Dict[str, Any]):
        """
        Update dashboard cache with new trade data
        
        Args:
            strategy_name: Strategy that generated trade
            trade: Trade dictionary
        """
        try:
            # Update trades list (keep last 100)
            self.dashboard_cache['trades'].append(trade)
            self.dashboard_cache['trades'] = self.dashboard_cache['trades'][-100:]
            
            # Update portfolio summary
            self.dashboard_cache['portfolio'] = self.portfolio_tracker.get_summary()
            
            # Update strategy stats
            if strategy_name not in self.dashboard_cache['strategies']:
                self.dashboard_cache['strategies'][strategy_name] = {
                    'trades': 0,
                    'total_pnl': 0
                }
            
            self.dashboard_cache['strategies'][strategy_name]['trades'] += 1
            self.dashboard_cache['strategies'][strategy_name]['total_pnl'] += trade.get('pnl', 0)
            
        except Exception as e:
            self.logger.log_error(f"Error updating dashboard cache: {e}")
    
    def _broadcast_update(self, trade: Dict[str, Any]):
        """
        Broadcast update via WebSocket
        
        Args:
            trade: Trade to broadcast
        """
        try:
            # Try to import and use WebSocket server if available
            from dashboard.websocket_server import live_data
            
            # Update live data
            live_data['trades'].append(trade)
            live_data['trades'] = live_data['trades'][-100:]  # Keep last 100
            live_data['portfolio'] = self.dashboard_cache['portfolio']
            live_data['strategies'] = self.dashboard_cache['strategies']
            
        except ImportError:
            # WebSocket server not available yet
            pass
        except Exception as e:
            self.logger.log_error(f"Error broadcasting update: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        return self.portfolio_tracker.get_summary()
    
    def get_recent_trades(self, limit: int = 100) -> list:
        """Get recent trades"""
        return self.trade_logger.get_recent_trades(limit)
    
    def get_all_trades(self) -> list:
        """Get all trades"""
        return self.trade_logger.get_all_trades()
    
    def get_strategy_stats(self, strategy_name: str) -> Dict[str, Any]:
        """Get stats for specific strategy"""
        trades = self.trade_logger.get_trades_by_strategy(strategy_name)
        
        if not trades:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'win_rate': 0
            }
        
        winning = [t for t in trades if t.get('pnl', 0) > 0]
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(trades) - len(winning),
            'win_rate': len(winning) / len(trades) * 100,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(trades)
        }
