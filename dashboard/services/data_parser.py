"""
Data Parser Service

Parses trading logs, opportunities, and other data files
to provide structured data for the dashboard.
"""

import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os


class DataParser:
    """Parse trading data from CSV logs and JSON files"""
    
    def __init__(self, logs_dir: Path):
        """
        Initialize data parser
        
        Args:
            logs_dir: Path to logs directory
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Sample data for testing (will be replaced with actual log parsing)
        self._sample_trades = self._generate_sample_trades()
        self._sample_opportunities = self._generate_sample_opportunities()
    
    def _generate_sample_trades(self) -> List[Dict[str, Any]]:
        """Generate sample trades for testing"""
        trades = []
        base_time = datetime.now() - timedelta(days=30)
        
        strategies = ['RSI Scalp', 'MACD Trend', 'Momentum', 'Arbitrage']
        symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'SPY']
        
        for i in range(127):
            entry_time = base_time + timedelta(hours=i*2)
            exit_time = entry_time + timedelta(hours=2, minutes=15)
            
            entry_price = 100 + (i % 50)
            is_win = (i % 3) != 0  # 66% win rate
            
            if is_win:
                exit_price = entry_price * (1 + (0.01 + (i % 5) * 0.005))
                pnl = (exit_price - entry_price) * 10
            else:
                exit_price = entry_price * (1 - (0.005 + (i % 3) * 0.003))
                pnl = (exit_price - entry_price) * 10
            
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            
            trades.append({
                'id': 127 - i,
                'symbol': symbols[i % len(symbols)],
                'strategy': strategies[i % len(strategies)],
                'entry_time': entry_time.isoformat(),
                'exit_time': exit_time.isoformat(),
                'duration_minutes': 135,
                'entry_price': round(entry_price, 2),
                'exit_price': round(exit_price, 2),
                'pnl_usd': round(pnl, 2),
                'pnl_pct': round(pnl_pct, 2),
                'status': 'closed',
                'outcome': 'win' if is_win else 'loss'
            })
        
        return trades
    
    def _generate_sample_opportunities(self) -> List[Dict[str, Any]]:
        """Generate sample opportunities for testing"""
        opportunities = []
        base_time = datetime.now() - timedelta(days=7)
        
        strategies = ['RSI Scalp', 'MACD Trend', 'Momentum', 'Arbitrage']
        symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN']
        
        for i in range(50):
            timestamp = base_time + timedelta(hours=i*3)
            acted_on = (i % 4) != 0
            
            opportunities.append({
                'id': i + 1,
                'timestamp': timestamp.isoformat(),
                'symbol': symbols[i % len(symbols)],
                'strategy': strategies[i % len(strategies)],
                'signal_type': 'BUY' if i % 2 == 0 else 'SELL',
                'confidence': round(0.60 + (i % 40) * 0.01, 2),
                'action_taken': acted_on,
                'outcome': 'win' if acted_on and (i % 3) != 0 else 'loss' if acted_on else None,
                'pnl_usd': round((10 + i % 20) * (1 if (i % 3) != 0 else -1), 2) if acted_on else None
            })
        
        return opportunities
    
    def get_trades(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        outcome: Optional[str] = None,
        page: int = 1,
        per_page: int = 25
    ) -> Dict[str, Any]:
        """
        Get filtered trades data
        
        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            symbol: Symbol filter
            strategy: Strategy filter
            outcome: Outcome filter (win/loss/breakeven)
            page: Page number for pagination
            per_page: Results per page
            
        Returns:
            Dictionary with trades data and metadata
        """
        # Filter trades
        filtered_trades = self._sample_trades.copy()
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            filtered_trades = [t for t in filtered_trades 
                             if datetime.fromisoformat(t['entry_time']) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            filtered_trades = [t for t in filtered_trades 
                             if datetime.fromisoformat(t['entry_time']) <= end]
        
        if symbol:
            filtered_trades = [t for t in filtered_trades if t['symbol'] == symbol]
        
        if strategy:
            filtered_trades = [t for t in filtered_trades if t['strategy'] == strategy]
        
        if outcome:
            filtered_trades = [t for t in filtered_trades if t['outcome'] == outcome]
        
        # Calculate summary stats
        total_pnl = sum(t['pnl_usd'] for t in filtered_trades)
        avg_pnl = total_pnl / len(filtered_trades) if filtered_trades else 0
        wins = [t for t in filtered_trades if t['pnl_usd'] > 0]
        losses = [t for t in filtered_trades if t['pnl_usd'] < 0]
        
        largest_win = max([t['pnl_usd'] for t in wins]) if wins else 0
        largest_loss = min([t['pnl_usd'] for t in losses]) if losses else 0
        
        # Paginate
        total_count = len(filtered_trades)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_trades = filtered_trades[start_idx:end_idx]
        
        return {
            'trades': paginated_trades,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'summary': {
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(avg_pnl, 2),
                'largest_win': round(largest_win, 2),
                'largest_loss': round(largest_loss, 2)
            }
        }
    
    def get_opportunities(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get opportunities data with filters
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            symbol: Symbol filter
            strategy: Strategy filter
            status: Status filter (acted/missed/pending)
            
        Returns:
            Dictionary with opportunities data
        """
        filtered_opps = self._sample_opportunities.copy()
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            filtered_opps = [o for o in filtered_opps 
                           if datetime.fromisoformat(o['timestamp']) >= start]
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            filtered_opps = [o for o in filtered_opps 
                           if datetime.fromisoformat(o['timestamp']) <= end]
        
        if symbol:
            filtered_opps = [o for o in filtered_opps if o['symbol'] == symbol]
        
        if strategy:
            filtered_opps = [o for o in filtered_opps if o['strategy'] == strategy]
        
        if status:
            if status == 'acted':
                filtered_opps = [o for o in filtered_opps if o['action_taken']]
            elif status == 'missed':
                filtered_opps = [o for o in filtered_opps if not o['action_taken']]
        
        # Calculate conversion rate
        total = len(filtered_opps)
        acted = len([o for o in filtered_opps if o['action_taken']])
        conversion_rate = (acted / total * 100) if total > 0 else 0
        
        return {
            'opportunities': filtered_opps,
            'total_count': total,
            'acted_count': acted,
            'missed_count': total - acted,
            'conversion_rate': round(conversion_rate, 2)
        }
    
    def get_all_trades(self) -> List[Dict[str, Any]]:
        """Get all trades without filtering"""
        return self._sample_trades
    
    def get_all_opportunities(self) -> List[Dict[str, Any]]:
        """Get all opportunities without filtering"""
        return self._sample_opportunities
