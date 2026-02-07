"""
Binance Public API Client
Free, no authentication required
Rate limit: 1200 requests/minute
"""

import requests
import time
from typing import Dict, Optional, List
from datetime import datetime


class BinanceClient:
    """Free Binance API client for real-time crypto prices"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    WEBSOCKET_URL = "wss://stream.binance.com:9443/ws"
    
    def __init__(self, rate_limit_per_minute: int = 1200):
        """
        Initialize Binance client
        
        Args:
            rate_limit_per_minute: Maximum requests per minute (default: 1200)
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
        if self.request_count >= self.rate_limit_per_minute - 10:
            wait_time = 60 - elapsed + 1
            if wait_time > 0:
                time.sleep(wait_time)
                self.request_count = 0
                self.request_window_start = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to Binance API
        
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
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a crypto symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT', 'ETHUSDT')
            
        Returns:
            Current price or None on error
        """
        # Normalize symbol to uppercase
        symbol = symbol.upper()
        
        # Add USDT if not present
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        data = self._make_request("/ticker/price", {"symbol": symbol})
        
        if data and 'price' in data:
            return float(data['price'])
        
        return None
    
    def get_ticker_24h(self, symbol: str) -> Optional[Dict]:
        """
        Get 24-hour ticker data including volume and price changes
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Ticker data dictionary or None on error
        """
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol = f"{symbol}USDT"
        
        data = self._make_request("/ticker/24hr", {"symbol": symbol})
        
        if data:
            return {
                'symbol': data.get('symbol'),
                'price': float(data.get('lastPrice', 0)),
                'volume': float(data.get('volume', 0)),
                'price_change': float(data.get('priceChange', 0)),
                'price_change_percent': float(data.get('priceChangePercent', 0)),
                'high': float(data.get('highPrice', 0)),
                'low': float(data.get('lowPrice', 0)),
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple symbols in one request
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary mapping symbols to prices
        """
        prices = {}
        
        # Binance allows fetching all prices in one request
        data = self._make_request("/ticker/price")
        
        if data and isinstance(data, list):
            # Normalize requested symbols
            normalized_symbols = set()
            for symbol in symbols:
                symbol = symbol.upper()
                if not symbol.endswith('USDT'):
                    symbol = f"{symbol}USDT"
                normalized_symbols.add(symbol)
            
            # Extract requested prices
            for item in data:
                symbol = item.get('symbol')
                if symbol in normalized_symbols:
                    prices[symbol] = float(item.get('price', 0))
        
        return prices
    
    def ping(self) -> bool:
        """
        Test connectivity to Binance API
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.BASE_URL}/ping", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Optional[Dict]:
        """
        Get exchange information for trading pairs
        
        Args:
            symbol: Optional symbol to get info for specific pair
            
        Returns:
            Exchange info dictionary or None on error
        """
        params = {}
        if symbol:
            symbol = symbol.upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            params['symbol'] = symbol
        
        return self._make_request("/exchangeInfo", params)
