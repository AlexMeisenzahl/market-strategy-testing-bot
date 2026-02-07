"""
CoinGecko Free API Client
- Crypto prices & market data
- 10-50 requests/minute (no key)
- Fallback for Binance
"""

import requests
import time
from typing import Dict, Optional, List
from datetime import datetime


class CoinGeckoClient:
    """Client for CoinGecko Free API"""
    
    # Symbol mapping from Binance to CoinGecko
    SYMBOL_MAP = {
        'BTCUSDT': 'bitcoin',
        'ETHUSDT': 'ethereum',
        'BNBUSDT': 'binancecoin',
        'ADAUSDT': 'cardano',
        'DOGEUSDT': 'dogecoin',
        'XRPUSDT': 'ripple',
        'DOTUSDT': 'polkadot',
        'UNIUSDT': 'uniswap',
        'LINKUSDT': 'chainlink',
        'MATICUSDT': 'matic-network'
    }
    
    def __init__(self):
        """Initialize CoinGecko client"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.last_request_time = 0
        self.min_request_interval = 1.2  # Rate limit: ~50 req/min
        
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _symbol_to_coin_id(self, symbol: str) -> str:
        """
        Convert Binance symbol to CoinGecko coin ID
        
        Args:
            symbol: Binance trading pair (e.g., 'BTCUSDT')
            
        Returns:
            CoinGecko coin ID (e.g., 'bitcoin')
        """
        return self.SYMBOL_MAP.get(symbol.upper(), symbol.lower().replace('usdt', ''))
    
    def get_price(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """
        Get current price (no auth required)
        
        Args:
            symbol: Trading pair symbol or coin ID
            
        Returns:
            Current price in USD, or None on error
        """
        try:
            self._rate_limit()
            
            coin_id = self._symbol_to_coin_id(symbol)
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if coin_id in data and 'usd' in data[coin_id]:
                return float(data[coin_id]['usd'])
            
            return None
            
        except Exception as e:
            print(f"Error fetching price from CoinGecko for {symbol}: {e}")
            return None
    
    def get_prices_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple coins in one request
        
        Args:
            symbols: List of trading pair symbols or coin IDs
            
        Returns:
            Dictionary mapping symbols to prices
        """
        try:
            self._rate_limit()
            
            coin_ids = [self._symbol_to_coin_id(s) for s in symbols]
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Map back to original symbols
            prices = {}
            for symbol, coin_id in zip(symbols, coin_ids):
                if coin_id in data and 'usd' in data[coin_id]:
                    prices[symbol] = float(data[coin_id]['usd'])
            
            return prices
            
        except Exception as e:
            print(f"Error fetching batch prices from CoinGecko: {e}")
            return {}
    
    def get_market_data(self, symbol: str = 'BTCUSDT') -> Optional[Dict]:
        """
        Get comprehensive market data for a coin
        
        Args:
            symbol: Trading pair symbol or coin ID
            
        Returns:
            Dictionary with market data, or None on error
        """
        try:
            self._rate_limit()
            
            coin_id = self._symbol_to_coin_id(symbol)
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': coin_id
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data:
                coin = data[0]
                return {
                    'symbol': coin['symbol'].upper() + 'USDT',
                    'price': float(coin['current_price']),
                    'market_cap': float(coin.get('market_cap', 0)),
                    'volume_24h': float(coin.get('total_volume', 0)),
                    'price_change_24h': float(coin.get('price_change_percentage_24h', 0)),
                    'high_24h': float(coin.get('high_24h', 0)),
                    'low_24h': float(coin.get('low_24h', 0)),
                    'circulating_supply': float(coin.get('circulating_supply', 0)),
                    'last_updated': coin.get('last_updated')
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching market data from CoinGecko for {symbol}: {e}")
            return None
    
    def get_market_chart(self, symbol: str = 'BTCUSDT', days: int = 7) -> Optional[List[Dict]]:
        """
        Get historical price chart data
        
        Args:
            symbol: Trading pair symbol or coin ID
            days: Number of days of historical data (1, 7, 14, 30, 90, 180, 365, max)
            
        Returns:
            List of price points with timestamps, or None on error
        """
        try:
            self._rate_limit()
            
            coin_id = self._symbol_to_coin_id(symbol)
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse price data
            prices = []
            for timestamp, price in data.get('prices', []):
                prices.append({
                    'timestamp': timestamp,
                    'date': datetime.fromtimestamp(timestamp / 1000).isoformat(),
                    'price': float(price)
                })
            
            return prices
            
        except Exception as e:
            print(f"Error fetching market chart from CoinGecko for {symbol}: {e}")
            return None
    
    def get_trending_coins(self) -> Optional[List[Dict]]:
        """
        Get trending cryptocurrencies
        
        Returns:
            List of trending coins with data, or None on error
        """
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/search/trending"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse trending coins
            trending = []
            for item in data.get('coins', []):
                coin = item.get('item', {})
                trending.append({
                    'id': coin.get('id'),
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'price_btc': float(coin.get('price_btc', 0))
                })
            
            return trending
            
        except Exception as e:
            print(f"Error fetching trending coins from CoinGecko: {e}")
            return None
    
    def search_coins(self, query: str) -> Optional[List[Dict]]:
        """
        Search for coins by name or symbol
        
        Args:
            query: Search query string
            
        Returns:
            List of matching coins, or None on error
        """
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/search"
            params = {'query': query}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse search results
            results = []
            for coin in data.get('coins', [])[:10]:  # Limit to 10 results
                results.append({
                    'id': coin.get('id'),
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'market_cap_rank': coin.get('market_cap_rank')
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching coins on CoinGecko: {e}")
            return None
