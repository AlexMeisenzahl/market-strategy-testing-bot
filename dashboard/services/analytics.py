"""
Analytics Service

Calculates performance metrics, statistics, and analytics
for the trading bot.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from dashboard.services.data_parser import DataParser


class AnalyticsService:
    """Calculate trading analytics and performance metrics"""
    
    def __init__(self, data_parser: DataParser):
        """
        Initialize analytics service
        
        Args:
            data_parser: Data parser instance
        """
        self.data_parser = data_parser
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """
        Get overview dashboard statistics
        
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
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
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
            'avg_win': round(gross_profit / len(wins), 2) if wins else 0,
            'avg_loss': round(gross_loss / len(losses), 2) if losses else 0
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
