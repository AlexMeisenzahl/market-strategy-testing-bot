"""
Data Parser Service

Parses trading logs, opportunities, and other data files
to provide structured data for the dashboard.
Reads from actual CSV files with fallback to sample data.
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
        
        # File paths
        self.trades_csv = self.logs_dir / 'trades.csv'
        self.opportunities_csv = self.logs_dir / 'opportunities.csv'
        
        # Cache for parsed data
        self._trades_cache = None
        self._opportunities_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 5  # Cache TTL in seconds
        
        # Sample data for testing (used as fallback)
        self._sample_trades = self._generate_sample_trades()
        self._sample_opportunities = self._generate_sample_opportunities()
    
    def _read_trades_from_csv(self) -> List[Dict[str, Any]]:
        """
        Read trades from CSV file
        
        Returns:
            List of trade dictionaries
        """
        trades = []
        
        if not self.trades_csv.exists():
            return None  # Return None to indicate file doesn't exist
        
        try:
            with open(self.trades_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Parse the trade data
                        trade = {
                            'id': int(row.get('id', 0)),
                            'symbol': row.get('symbol', ''),
                            'strategy': row.get('strategy', ''),
                            'entry_time': row.get('entry_time', ''),
                            'exit_time': row.get('exit_time', ''),
                            'duration_minutes': int(float(row.get('duration_minutes', 0))),
                            'entry_price': float(row.get('entry_price', 0)),
                            'exit_price': float(row.get('exit_price', 0)),
                            'pnl_usd': float(row.get('pnl_usd', 0)),
                            'pnl_pct': float(row.get('pnl_pct', 0)),
                            'status': row.get('status', 'closed'),
                            'outcome': 'win' if float(row.get('pnl_usd', 0)) > 0 else 'loss' if float(row.get('pnl_usd', 0)) < 0 else 'breakeven'
                        }
                        trades.append(trade)
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Skipping malformed trade row: {e}")
                        continue
        except Exception as e:
            print(f"Error reading trades CSV: {e}")
            return None
        
        return trades
    
    def _read_opportunities_from_csv(self) -> List[Dict[str, Any]]:
        """
        Read opportunities from CSV file
        
        Returns:
            List of opportunity dictionaries
        """
        opportunities = []
        
        if not self.opportunities_csv.exists():
            return None  # Return None to indicate file doesn't exist
        
        try:
            with open(self.opportunities_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Parse the opportunity data
                        opportunity = {
                            'id': int(row.get('id', 0)),
                            'timestamp': row.get('timestamp', ''),
                            'symbol': row.get('symbol', ''),
                            'strategy': row.get('strategy', ''),
                            'signal_type': row.get('signal_type', 'BUY'),
                            'confidence': float(row.get('confidence', 0)),
                            'action_taken': row.get('action_taken', 'false').lower() == 'true',
                            'outcome': row.get('outcome', None),
                            'pnl_usd': float(row.get('pnl_usd', 0)) if row.get('pnl_usd') else None
                        }
                        opportunities.append(opportunity)
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Skipping malformed opportunity row: {e}")
                        continue
        except Exception as e:
            print(f"Error reading opportunities CSV: {e}")
            return None
        
        return opportunities
    
    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed"""
        if self._cache_timestamp is None:
            return True
        
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed > self._cache_ttl
    
    def _get_trades_with_cache(self) -> List[Dict[str, Any]]:
        """Get trades with caching"""
        if self._should_refresh_cache():
            # Try to read from CSV
            csv_trades = self._read_trades_from_csv()
            
            if csv_trades is not None and len(csv_trades) > 0:
                self._trades_cache = csv_trades
            else:
                # Fall back to sample data
                self._trades_cache = self._sample_trades
            
            self._cache_timestamp = datetime.now()
        
        return self._trades_cache
    
    def _get_opportunities_with_cache(self) -> List[Dict[str, Any]]:
        """Get opportunities with caching"""
        if self._opportunities_cache is None or self._should_refresh_cache():
            # Try to read from CSV
            csv_opportunities = self._read_opportunities_from_csv()
            
            if csv_opportunities is not None and len(csv_opportunities) > 0:
                self._opportunities_cache = csv_opportunities
            else:
                # Fall back to sample data
                self._opportunities_cache = self._sample_opportunities
        
        return self._opportunities_cache
    
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
        # Get trades from cache (which will read from CSV or use sample data)
        all_trades = self._get_trades_with_cache()
        
        # Filter trades
        filtered_trades = all_trades.copy()
        
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
        # Get opportunities from cache (which will read from CSV or use sample data)
        all_opportunities = self._get_opportunities_with_cache()
        
        filtered_opps = all_opportunities.copy()
        
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
        return self._get_trades_with_cache()
    
    def get_all_opportunities(self) -> List[Dict[str, Any]]:
        """Get all opportunities without filtering"""
        return self._get_opportunities_with_cache()
