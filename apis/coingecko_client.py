"""
CoinGecko Public API Client
Free, no authentication required
Rate limit: 50 requests/minute (free tier)
Coverage: 13,000+ cryptocurrencies
"""

import requests
import time
from typing import Dict, Optional, List


class CoinGeckoClient:
    """Free CoinGecko API client for crypto market data"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Map common symbols to CoinGecko IDs
    SYMBOL_TO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'USDT': 'tether',
        'USDC': 'usd-coin',
        'BNB': 'binancecoin',
        'ADA': 'cardano',
        'DOGE': 'dogecoin',
        'XRP': 'ripple',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'AVAX': 'avalanche-2',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'ATOM': 'cosmos'
    }
    
    def __init__(self, rate_limit_per_minute: int = 50):
        """
        Initialize CoinGecko client
        
        Args:
            rate_limit_per_minute: Maximum requests per minute (default: 50)
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self.request_count = 0
        self.request_window_start = time.time()
        self.timeout = 10
        
    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.request_window_start
        
        # Reset counter after 60 seconds
        if elapsed >= 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # If approaching limit, wait
        if self.request_count >= self.rate_limit_per_minute - 5:
            wait_time = 60 - elapsed + 1
            if wait_time > 0:
                time.sleep(wait_time)
                self.request_count = 0
                self.request_window_start = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to CoinGecko API
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response or None on error
        """
        self._check_rate_limit()
        
        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = requests.get(url, params=params, timeout=self.timeout)
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None
    
    def _symbol_to_id(self, symbol: str) -> str:
        """
        Convert symbol to CoinGecko ID
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            CoinGecko ID
        """
        symbol = symbol.upper().replace('USDT', '').replace('USD', '')
        return self.SYMBOL_TO_ID.get(symbol, symbol.lower())
    
    def get_price(self, symbol: str, vs_currency: str = 'usd') -> Optional[float]:
        """
        Get current price for a crypto symbol
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            vs_currency: Currency to compare against (default: 'usd')
            
        Returns:
            Current price or None on error
        """
        coin_id = self._symbol_to_id(symbol)
        
        data = self._make_request(
            "/simple/price",
            {"ids": coin_id, "vs_currencies": vs_currency}
        )
        
        if data and coin_id in data:
            return float(data[coin_id].get(vs_currency, 0))
        
        return None
    
    def get_multiple_prices(self, symbols: List[str], vs_currency: str = 'usd') -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies
        
        Args:
            symbols: List of crypto symbols
            vs_currency: Currency to compare against (default: 'usd')
            
        Returns:
            Dictionary mapping symbols to prices
        """
        # Convert symbols to CoinGecko IDs
        coin_ids = [self._symbol_to_id(symbol) for symbol in symbols]
        ids_param = ','.join(coin_ids)
        
        data = self._make_request(
            "/simple/price",
            {"ids": ids_param, "vs_currencies": vs_currency}
        )
        
        prices = {}
        if data:
            for i, symbol in enumerate(symbols):
                coin_id = coin_ids[i]
                if coin_id in data:
                    prices[symbol.upper()] = float(data[coin_id].get(vs_currency, 0))
        
        return prices
    
    def get_market_data(self, symbol: str, vs_currency: str = 'usd') -> Optional[Dict]:
        """
        Get comprehensive market data including volume, market cap, and 24h changes
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            vs_currency: Currency to compare against (default: 'usd')
            
        Returns:
            Market data dictionary or None on error
        """
        coin_id = self._symbol_to_id(symbol)
        
        data = self._make_request(
            "/coins/markets",
            {
                "vs_currency": vs_currency,
                "ids": coin_id,
                "order": "market_cap_desc",
                "per_page": 1,
                "page": 1,
                "sparkline": False
            }
        )
        
        if data and len(data) > 0:
            item = data[0]
            return {
                'symbol': item.get('symbol', '').upper(),
                'price': float(item.get('current_price', 0)),
                'market_cap': float(item.get('market_cap', 0)),
                'volume_24h': float(item.get('total_volume', 0)),
                'price_change_24h': float(item.get('price_change_24h', 0)),
                'price_change_percentage_24h': float(item.get('price_change_percentage_24h', 0)),
                'high_24h': float(item.get('high_24h', 0)),
                'low_24h': float(item.get('low_24h', 0)),
                'circulating_supply': float(item.get('circulating_supply', 0)),
                'total_supply': float(item.get('total_supply', 0))
            }
        
        return None
    
    def ping(self) -> bool:
        """
        Test connectivity to CoinGecko API
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            data = self._make_request("/ping")
            return data is not None and 'gecko_says' in data
        except Exception:
            return False
    
    def search_coin(self, query: str) -> Optional[List[Dict]]:
        """
        Search for a cryptocurrency by name or symbol
        
        Args:
            query: Search query (name or symbol)
            
        Returns:
            List of matching coins or None on error
        """
        data = self._make_request("/search", {"query": query})
        
        if data and 'coins' in data:
            return data['coins']
        
        return None
