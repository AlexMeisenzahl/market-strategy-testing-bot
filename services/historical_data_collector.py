"""
Historical Data Collector

Collects cryptocurrency and Polymarket historical price data
for backtesting and analysis purposes.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from database.models import CryptoPriceHistory, PolymarketHistory


class HistoricalDataCollector:
    """Collector for historical price data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        
    def collect_crypto_history(self, symbol: str, days: int = 365) -> Dict:
        """
        Collect cryptocurrency price history from CoinGecko
        
        Args:
            symbol: Crypto symbol (e.g., 'bitcoin', 'ethereum')
            days: Number of days of history to collect
            
        Returns:
            Dict with collection results
        """
        self.logger.info(f"Collecting {days} days of {symbol} price history...")
        
        try:
            # CoinGecko free API - market chart data
            url = f"{self.coingecko_api}/coins/{symbol.lower()}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if days <= 90 else 'daily'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract prices, volumes, and market caps
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            market_caps = data.get('market_caps', [])
            
            # Prepare records for bulk insert
            records = []
            for i, price_data in enumerate(prices):
                timestamp_ms, price_usd = price_data
                timestamp = int(timestamp_ms / 1000)  # Convert to seconds
                
                volume = volumes[i][1] if i < len(volumes) else None
                market_cap = market_caps[i][1] if i < len(market_caps) else None
                
                records.append({
                    'symbol': symbol,
                    'price_usd': price_usd,
                    'volume': volume,
                    'market_cap': market_cap,
                    'timestamp': timestamp
                })
            
            # Bulk insert into database
            inserted_count = CryptoPriceHistory.bulk_insert(records)
            
            self.logger.info(
                f"✓ Collected {inserted_count} {symbol} price records"
            )
            
            return {
                'success': True,
                'symbol': symbol,
                'records_collected': inserted_count,
                'date_range': {
                    'start': datetime.fromtimestamp(records[0]['timestamp']).isoformat(),
                    'end': datetime.fromtimestamp(records[-1]['timestamp']).isoformat()
                }
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to collect {symbol} history: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Unexpected error collecting {symbol} history: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def collect_polymarket_history(self, market_id: str, days: int = 90) -> Dict:
        """
        Collect Polymarket market history
        
        Args:
            market_id: Polymarket market ID
            days: Number of days of history to collect
            
        Returns:
            Dict with collection results
            
        Note: This is a placeholder - Polymarket historical data collection
        would require integration with their API or subgraph
        """
        self.logger.info(
            f"Collecting {days} days of Polymarket history for {market_id}..."
        )
        
        try:
            # Placeholder - in production, this would call Polymarket API/Subgraph
            # For now, we'll create synthetic data for testing
            records = []
            end_time = datetime.utcnow()
            
            for i in range(days * 24):  # Hourly data
                timestamp = int((end_time - timedelta(hours=i)).timestamp())
                
                # Synthetic prices (would be real API data in production)
                yes_price = 0.5 + (i % 50) / 100  # Varies between 0.5-1.0
                no_price = 1.0 - yes_price
                
                records.append({
                    'market_id': market_id,
                    'yes_price': yes_price,
                    'no_price': no_price,
                    'volume': 1000 + (i * 10),
                    'liquidity': 5000 + (i * 50),
                    'timestamp': timestamp
                })
            
            # Insert into database
            conn = PolymarketHistory.get_connection()
            cursor = conn.cursor()
            
            for record in records:
                PolymarketHistory.insert(
                    market_id=record['market_id'],
                    yes_price=record['yes_price'],
                    no_price=record['no_price'],
                    volume=record['volume'],
                    liquidity=record['liquidity'],
                    timestamp=record['timestamp']
                )
            
            self.logger.info(
                f"✓ Collected {len(records)} Polymarket price records"
            )
            
            return {
                'success': True,
                'market_id': market_id,
                'records_collected': len(records),
                'date_range': {
                    'start': datetime.fromtimestamp(records[-1]['timestamp']).isoformat(),
                    'end': datetime.fromtimestamp(records[0]['timestamp']).isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect Polymarket history: {e}")
            return {
                'success': False,
                'market_id': market_id,
                'error': str(e)
            }
    
    def fill_gaps(self, symbol: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Fill gaps in historical data
        
        Args:
            symbol: Symbol to check for gaps
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Dict with gap filling results
        """
        self.logger.info(f"Checking for gaps in {symbol} data...")
        
        try:
            # Get existing data
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())
            
            existing_data = CryptoPriceHistory.get_history(
                symbol, start_ts, end_ts
            )
            
            if not existing_data:
                # No data exists, collect everything
                days = (end_date - start_date).days
                return self.collect_crypto_history(symbol, days)
            
            # Check for gaps (more than 2 hours between records)
            gaps = []
            for i in range(len(existing_data) - 1):
                time_diff = existing_data[i+1]['timestamp'] - existing_data[i]['timestamp']
                if time_diff > 7200:  # 2 hours
                    gaps.append({
                        'start': existing_data[i]['timestamp'],
                        'end': existing_data[i+1]['timestamp']
                    })
            
            if not gaps:
                self.logger.info(f"No gaps found in {symbol} data")
                return {
                    'success': True,
                    'symbol': symbol,
                    'gaps_filled': 0
                }
            
            # Fill gaps
            self.logger.info(f"Found {len(gaps)} gaps in {symbol} data, filling...")
            total_filled = 0
            
            for gap in gaps:
                gap_start = datetime.fromtimestamp(gap['start'])
                gap_end = datetime.fromtimestamp(gap['end'])
                gap_days = (gap_end - gap_start).days + 1
                
                result = self.collect_crypto_history(symbol, gap_days)
                if result['success']:
                    total_filled += result['records_collected']
            
            self.logger.info(f"✓ Filled {total_filled} records in {len(gaps)} gaps")
            
            return {
                'success': True,
                'symbol': symbol,
                'gaps_filled': total_filled,
                'gap_count': len(gaps)
            }
            
        except Exception as e:
            self.logger.error(f"Error filling gaps: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def update_latest_data(self, symbols: List[str]) -> Dict:
        """
        Update with latest data for given symbols
        
        Args:
            symbols: List of symbols to update
            
        Returns:
            Dict with update results
        """
        self.logger.info(f"Updating latest data for {len(symbols)} symbols...")
        
        results = []
        for symbol in symbols:
            # Collect last 2 days to ensure we have latest
            result = self.collect_crypto_history(symbol, days=2)
            results.append(result)
            
            # Rate limiting - CoinGecko free tier allows 10-30 calls/min
            time.sleep(2)
        
        successful = sum(1 for r in results if r['success'])
        
        self.logger.info(
            f"✓ Updated {successful}/{len(symbols)} symbols"
        )
        
        return {
            'success': True,
            'updated_count': successful,
            'total_count': len(symbols),
            'results': results
        }
    
    def get_available_symbols(self) -> List[str]:
        """
        Get list of available crypto symbols from CoinGecko
        
        Returns:
            List of symbol IDs
        """
        try:
            url = f"{self.coingecko_api}/coins/list"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            coins = response.json()
            # Return top 100 by market cap (simplified)
            return [coin['id'] for coin in coins[:100]]
            
        except Exception as e:
            self.logger.error(f"Error fetching available symbols: {e}")
            # Return common symbols as fallback
            return ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana']


# Global instance
historical_data_collector = HistoricalDataCollector()
