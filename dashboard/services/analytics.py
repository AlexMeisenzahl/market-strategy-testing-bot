"""
Analytics Service

Calculates performance metrics, statistics, and analytics
for the trading bot including Sharpe ratio, max drawdown, and more.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from dashboard.services.data_parser import DataParser
import math


class AnalyticsService:
    """Calculate trading analytics and performance metrics"""
    
    def __init__(self, data_parser: DataParser):
        """
        Initialize analytics service
        
        Args:
            data_parser: Data parser instance
        """
        self.data_parser = data_parser
    
    def calculate_sharpe_ratio(self, trades: List[Dict[str, Any]], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio for the trading strategy
        
        Args:
            trades: List of trade dictionaries
            risk_free_rate: Annual risk-free rate (default 2%)
            
        Returns:
            Sharpe ratio
        """
        if not trades or len(trades) < 2:
            return 0.0
        
        # Calculate daily returns
        returns = [t['pnl_pct'] / 100 for t in trades]  # Convert percentage to decimal
        
        if not returns:
            return 0.0
        
        # Calculate mean and std of returns
        mean_return = sum(returns) / len(returns)
        
        # Calculate standard deviation
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance) if variance > 0 else 0
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming 252 trading days per year)
        daily_risk_free = risk_free_rate / 252
        sharpe_ratio = (mean_return - daily_risk_free) / std_return * math.sqrt(252)
        
        return sharpe_ratio
    
    def calculate_max_drawdown(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate maximum drawdown from peak equity
        
        Args:
            trades: List of trade dictionaries sorted by time
            
        Returns:
            Dictionary with max drawdown info
        """
        if not trades:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'peak_value': 0.0,
                'trough_value': 0.0
            }
        
        # Calculate cumulative equity curve
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        peak_value = 0
        trough_value = 0
        
        for trade in trades:
            cumulative_pnl += trade['pnl_usd']
            
            # Update peak if current value is higher
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            
            # Calculate drawdown from peak
            drawdown = peak - cumulative_pnl
            
            # Update max drawdown if current is larger
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                peak_value = peak
                trough_value = cumulative_pnl
        
        # Calculate percentage drawdown
        max_drawdown_pct = (max_drawdown / peak_value * 100) if peak_value > 0 else 0
        
        return {
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'peak_value': round(peak_value, 2),
            'trough_value': round(trough_value, 2)
        }
    
    def calculate_profit_factor(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate profit factor (gross profit / gross loss)
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Profit factor
        """
        wins = [t for t in trades if t['pnl_usd'] > 0]
        losses = [t for t in trades if t['pnl_usd'] < 0]
        
        gross_profit = sum(t['pnl_usd'] for t in wins)
        gross_loss = abs(sum(t['pnl_usd'] for t in losses))
        
        return (gross_profit / gross_loss) if gross_loss > 0 else 0
    
    def calculate_win_loss_ratio(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate win/loss ratio metrics
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Dictionary with win/loss metrics
        """
        wins = [t for t in trades if t['pnl_usd'] > 0]
        losses = [t for t in trades if t['pnl_usd'] < 0]
        
        avg_win = sum(t['pnl_usd'] for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t['pnl_usd'] for t in losses) / len(losses)) if losses else 0
        
        win_loss_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0
        
        return {
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'win_loss_ratio': round(win_loss_ratio, 2),
            'total_wins': len(wins),
            'total_losses': len(losses)
        }
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """
        Get overview dashboard statistics with advanced metrics
        
        Returns:
            Dictionary with key metrics
        """
        trades = self.data_parser.get_all_trades()
        opportunities = self.data_parser.get_all_opportunities()
        
        # Calculate P&L metrics
        total_pnl = sum(t['pnl_usd'] for t in trades)
        wins = [t for t in trades if t['pnl_usd'] > 0]
        losses = [t for t in trades if t['pnl_usd'] < 0]
        
        win_rate = (len(wins) / len(trades) * 100) if trades else 0
        
        # Calculate profit factor
        gross_profit = sum(t['pnl_usd'] for t in wins)
        gross_loss = abs(sum(t['pnl_usd'] for t in losses))
        profit_factor = self.calculate_profit_factor(trades)
        
        # Calculate average trade duration
        avg_duration = sum(t['duration_minutes'] for t in trades) / len(trades) if trades else 0
        
        # Get today's opportunities
        today = datetime.now().date()
        today_opps = [o for o in opportunities 
                     if datetime.fromisoformat(o['timestamp']).date() == today]
        
        # Find best performing strategy
        strategy_pnl = {}
        for trade in trades:
            strategy = trade['strategy']
            if strategy not in strategy_pnl:
                strategy_pnl[strategy] = 0
            strategy_pnl[strategy] += trade['pnl_usd']
        
        best_strategy = max(strategy_pnl.items(), key=lambda x: x[1])[0] if strategy_pnl else 'N/A'
        
        # Active trades (currently none in our sample data)
        active_trades = [t for t in trades if t['status'] == 'open']
        
        # Calculate percentage changes (comparing to yesterday)
        yesterday = datetime.now() - timedelta(days=1)
        recent_trades = [t for t in trades 
                        if datetime.fromisoformat(t['entry_time']) >= yesterday]
        recent_pnl = sum(t['pnl_usd'] for t in recent_trades)
        
        # Simplified percentage (would need historical data for accurate calculation)
        pnl_change_pct = (recent_pnl / abs(total_pnl) * 100) if total_pnl != 0 else 0
        
        # Calculate advanced metrics
        sharpe_ratio = self.calculate_sharpe_ratio(trades)
        max_drawdown_info = self.calculate_max_drawdown(sorted(trades, key=lambda x: x['entry_time']))
        win_loss_info = self.calculate_win_loss_ratio(trades)
        
        return {
            'total_pnl': round(total_pnl, 2),
            'pnl_change_pct': round(pnl_change_pct, 2),
            'win_rate': round(win_rate, 2),
            'active_trades': len(active_trades),
            'today_opportunities': len(today_opps),
            'total_trades': len(trades),
            'profit_factor': round(profit_factor, 2),
            'avg_trade_duration': round(avg_duration, 2),
            'best_strategy': best_strategy,
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
            'largest_win': round(max([t['pnl_usd'] for t in wins]), 2) if wins else 0,
            'largest_loss': round(min([t['pnl_usd'] for t in losses]), 2) if losses else 0,
            'avg_win': win_loss_info['avg_win'],
            'avg_loss': win_loss_info['avg_loss'],
            'win_loss_ratio': win_loss_info['win_loss_ratio'],
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': max_drawdown_info['max_drawdown'],
            'max_drawdown_pct': max_drawdown_info['max_drawdown_pct']
        }
    
    def get_strategy_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance statistics by strategy
        
        Returns:
            Dictionary with stats for each strategy
        """
        trades = self.data_parser.get_all_trades()
        
        strategy_stats = {}
        
        for trade in trades:
            strategy = trade['strategy']
            
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'total_trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'total_pnl': 0,
                    'gross_profit': 0,
                    'gross_loss': 0
                }
            
            stats = strategy_stats[strategy]
            stats['total_trades'] += 1
            stats['total_pnl'] += trade['pnl_usd']
            
            if trade['pnl_usd'] > 0:
                stats['wins'] += 1
                stats['gross_profit'] += trade['pnl_usd']
            else:
                stats['losses'] += 1
                stats['gross_loss'] += abs(trade['pnl_usd'])
        
        # Calculate derived metrics
        for strategy, stats in strategy_stats.items():
            stats['win_rate'] = (stats['wins'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
            stats['profit_factor'] = (stats['gross_profit'] / stats['gross_loss']) if stats['gross_loss'] > 0 else 0
            stats['avg_pnl'] = stats['total_pnl'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
            
            # Round values
            for key in ['total_pnl', 'gross_profit', 'gross_loss', 'win_rate', 'profit_factor', 'avg_pnl']:
                stats[key] = round(stats[key], 2)
        
        return strategy_stats
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent trading activity
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities
        """
        trades = self.data_parser.get_all_trades()
        opportunities = self.data_parser.get_all_opportunities()
        
        # Combine and sort by timestamp
        activities = []
        
        # Add trades
        for trade in trades[:limit]:
            activities.append({
                'type': 'trade',
                'timestamp': trade['exit_time'],
                'description': f"{trade['symbol']} - {trade['strategy']}",
                'pnl': trade['pnl_usd'],
                'outcome': trade['outcome']
            })
        
        # Add opportunities
        for opp in opportunities[:limit]:
            if opp['action_taken']:
                activities.append({
                    'type': 'opportunity',
                    'timestamp': opp['timestamp'],
                    'description': f"{opp['symbol']} - {opp['strategy']}",
                    'confidence': opp['confidence'],
                    'acted': True
                })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return activities[:limit]
