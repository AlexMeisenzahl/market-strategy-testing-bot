"""
Portfolio Management System
Manages overall portfolio, risk allocation, and performance tracking
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import logging
from services.position_tracker import position_tracker, Position


@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot at a point in time"""
    timestamp: datetime
    total_value: float
    cash_balance: float
    positions_value: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    num_positions: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_value': self.total_value,
            'cash_balance': self.cash_balance,
            'positions_value': self.positions_value,
            'total_pnl': self.total_pnl,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'num_positions': self.num_positions
        }


class PortfolioManager:
    """Portfolio management system"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.cash_balance = initial_balance
        self.snapshots: List[PortfolioSnapshot] = []
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.utcnow()
    
    def get_current_value(self) -> float:
        """Get current portfolio value"""
        open_positions = position_tracker.get_open_positions()
        positions_value = sum(p.size for p in open_positions)
        return self.cash_balance + positions_value
    
    def get_realized_pnl(self) -> float:
        """Get realized profit/loss from closed positions"""
        closed_positions = position_tracker.get_closed_positions()
        return sum(
            p.actual_profit for p in closed_positions
            if p.actual_profit is not None
        )
    
    def get_unrealized_pnl(self) -> float:
        """Get unrealized profit/loss from open positions"""
        open_positions = position_tracker.get_open_positions()
        return sum(p.expected_profit for p in open_positions)
    
    def get_total_pnl(self) -> float:
        """Get total profit/loss"""
        return self.get_realized_pnl() + self.get_unrealized_pnl()
    
    def get_return_percentage(self) -> float:
        """Get return percentage"""
        current_value = self.get_current_value()
        return ((current_value - self.initial_balance) / self.initial_balance) * 100
    
    def allocate_capital(self, size: float) -> bool:
        """Allocate capital for a new position"""
        if size > self.cash_balance:
            self.logger.warning(f"Insufficient funds: ${size:.2f} requested, ${self.cash_balance:.2f} available")
            return False
        
        self.cash_balance -= size
        return True
    
    def release_capital(self, size: float, profit: float = 0.0):
        """Release capital from closed position"""
        self.cash_balance += size + profit
    
    def take_snapshot(self) -> PortfolioSnapshot:
        """Take a portfolio snapshot"""
        open_positions = position_tracker.get_open_positions()
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime.utcnow(),
            total_value=self.get_current_value(),
            cash_balance=self.cash_balance,
            positions_value=sum(p.size for p in open_positions),
            total_pnl=self.get_total_pnl(),
            realized_pnl=self.get_realized_pnl(),
            unrealized_pnl=self.get_unrealized_pnl(),
            num_positions=len(open_positions)
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        stats = position_tracker.get_position_stats()
        
        # Calculate win rate
        closed_positions = position_tracker.get_closed_positions()
        winning_trades = sum(1 for p in closed_positions if p.actual_profit and p.actual_profit > 0)
        win_rate = (winning_trades / len(closed_positions) * 100) if closed_positions else 0.0
        
        # Calculate average profit per trade
        avg_profit = (
            stats['total_realized_profit'] / len(closed_positions)
            if closed_positions else 0.0
        )
        
        # Calculate Sharpe ratio (simplified)
        returns = self.get_return_percentage()
        sharpe_ratio = returns / 10.0 if returns > 0 else 0.0  # Simplified
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Time-based metrics
        runtime = datetime.utcnow() - self.start_time
        runtime_hours = runtime.total_seconds() / 3600
        
        return {
            'portfolio_value': self.get_current_value(),
            'cash_balance': self.cash_balance,
            'total_pnl': self.get_total_pnl(),
            'realized_pnl': self.get_realized_pnl(),
            'unrealized_pnl': self.get_unrealized_pnl(),
            'return_percentage': self.get_return_percentage(),
            'win_rate': win_rate,
            'total_trades': len(closed_positions),
            'winning_trades': winning_trades,
            'losing_trades': len(closed_positions) - winning_trades,
            'avg_profit_per_trade': avg_profit,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'open_positions': stats['open_positions'],
            'runtime_hours': runtime_hours,
        }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.snapshots:
            return 0.0
        
        peak = self.initial_balance
        max_drawdown = 0.0
        
        for snapshot in self.snapshots:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
            
            drawdown = (peak - snapshot.total_value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance broken down by strategy"""
        strategies = {}
        
        for position in position_tracker.get_all_positions():
            strategy = position.strategy
            
            if strategy not in strategies:
                strategies[strategy] = {
                    'total_positions': 0,
                    'open_positions': 0,
                    'closed_positions': 0,
                    'total_pnl': 0.0,
                    'win_rate': 0.0,
                    'avg_profit': 0.0
                }
            
            strategies[strategy]['total_positions'] += 1
            
            if position.status == 'open':
                strategies[strategy]['open_positions'] += 1
            elif position.status == 'closed':
                strategies[strategy]['closed_positions'] += 1
                if position.actual_profit:
                    strategies[strategy]['total_pnl'] += position.actual_profit
        
        # Calculate win rates and averages
        for strategy, data in strategies.items():
            closed = data['closed_positions']
            if closed > 0:
                winning = sum(
                    1 for p in position_tracker.get_positions_by_strategy(strategy)
                    if p.status == 'closed' and p.actual_profit and p.actual_profit > 0
                )
                data['win_rate'] = (winning / closed) * 100
                data['avg_profit'] = data['total_pnl'] / closed
        
        return strategies
    
    def get_daily_pnl(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily P&L for the last N days"""
        daily_pnl = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            
            # Find positions closed on this day
            day_positions = [
                p for p in position_tracker.get_closed_positions()
                if p.exit_time and p.exit_time.date() == date.date()
            ]
            
            day_pnl = sum(
                p.actual_profit for p in day_positions
                if p.actual_profit is not None
            )
            
            daily_pnl.append({
                'date': date.strftime('%Y-%m-%d'),
                'pnl': day_pnl,
                'trades': len(day_positions)
            })
        
        return list(reversed(daily_pnl))
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export portfolio state to dictionary"""
        return {
            'initial_balance': self.initial_balance,
            'current_value': self.get_current_value(),
            'cash_balance': self.cash_balance,
            'performance_metrics': self.get_performance_metrics(),
            'strategy_performance': self.get_strategy_performance(),
            'daily_pnl': self.get_daily_pnl(),
        }


# Global instance
portfolio_manager = PortfolioManager()
