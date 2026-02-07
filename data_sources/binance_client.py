"""
Binance Client - WebSocket + REST API for Real-Time Crypto Prices

Provides:
- Real-time price streams via WebSocket (1200 req/min, FREE)
- Historical OHLCV data via REST API
- <100ms latency for live prices
- Used by Bloomberg Terminal, CoinMarketCap, TradingView

No API keys required for public data.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from threading import Thread, Lock
import requests

try:
    import websockets
except ImportError:
    websockets = None


class BinanceClient:
    """Binance WebSocket + REST API Client for Real-Time Crypto Prices"""
    
    # Public Binance API endpoints (no authentication required)
    REST_BASE_URL = "https://api.binance.com/api/v3"
    WS_BASE_URL = "wss://stream.binance.com:9443/ws"
    
    # Rate limits (generous free tier)
    MAX_REQUESTS_PER_MINUTE = 1200
    MAX_CONNECTIONS = 300
    
    def __init__(self, symbols: Optional[List[str]] = None):
        """
        Initialize Binance client
        
        Args:
            symbols: List of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])
                    Defaults to major cryptos
        """
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
        self.prices: Dict[str, Dict[str, Any]] = {}
        self.price_lock = Lock()
        
        # WebSocket state
        self.ws_connection = None
        self.ws_thread: Optional[Thread] = None
        self.ws_running = False
        self.callbacks: List[Callable] = []
        
        # Rate limiting
        self.request_times: List[datetime] = []
        
        # Connection health
        self.last_update: Optional[datetime] = None
        self.connection_errors = 0
        
    def start_websocket(self, callback: Optional[Callable] = None) -> bool:
        """
        Start WebSocket connection for real-time price updates
        
        Args:
            callback: Optional callback function called on each price update
                     Signature: callback(symbol: str, price: float, data: dict)
        
        Returns:
            True if WebSocket started successfully, False otherwise
        """
        if websockets is None:
            print("Warning: websockets library not installed. WebSocket features disabled.")
            print("Install with: pip install websockets")
            return False
        
        if self.ws_running:
            return True
        
        if callback:
            self.callbacks.append(callback)
        
        self.ws_running = True
        self.ws_thread = Thread(target=self._ws_loop, daemon=True)
        self.ws_thread.start()
        
        # Wait for initial connection
        time.sleep(1)
        
        return self.ws_connection is not None
    
    def stop_websocket(self) -> None:
        """Stop WebSocket connection"""
        self.ws_running = False
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
    
    def _ws_loop(self) -> None:
        """WebSocket event loop (runs in separate thread)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._ws_handler())
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            loop.close()
    
    async def _ws_handler(self) -> None:
        """WebSocket connection handler"""
        # Build stream URL for multiple symbols
        streams = [f"{symbol.lower()}@ticker" for symbol in self.symbols]
        stream_url = f"{self.WS_BASE_URL}/{'/'.join(streams)}"
        
        retry_count = 0
        max_retries = 5
        
        while self.ws_running and retry_count < max_retries:
            try:
                async with websockets.connect(stream_url) as websocket:
                    self.ws_connection = websocket
                    self.connection_errors = 0
                    retry_count = 0
                    
                    print(f"WebSocket connected: {len(self.symbols)} symbols")
                    
                    while self.ws_running:
                        try:
                            message = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=30.0
                            )
                            self._process_ws_message(message)
                        except asyncio.TimeoutError:
                            # Send ping to keep connection alive
                            await websocket.ping()
                        
            except Exception as e:
                self.connection_errors += 1
                retry_count += 1
                print(f"WebSocket connection error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        
        self.ws_connection = None
    
    def _process_ws_message(self, message: str) -> None:
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Handle single ticker update
            if 's' in data and 'c' in data:
                symbol = data['s']
                price = float(data['c'])
                
                # Update price cache
                with self.price_lock:
                    self.prices[symbol] = {
                        'price': price,
                        'timestamp': datetime.now(),
                        'volume_24h': float(data.get('v', 0)),
                        'price_change_24h': float(data.get('p', 0)),
                        'price_change_pct_24h': float(data.get('P', 0)),
                        'high_24h': float(data.get('h', 0)),
                        'low_24h': float(data.get('l', 0))
                    }
                    self.last_update = datetime.now()
                
                # Call registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(symbol, price, data)
                    except Exception as e:
                        print(f"Callback error: {e}")
        
        except json.JSONDecodeError:
            pass  # Ignore invalid JSON
        except Exception as e:
            print(f"Message processing error: {e}")
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get latest price for a symbol (from WebSocket cache or REST API)
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
        
        Returns:
            Current price or None if unavailable
        """
        # Try WebSocket cache first (fastest)
        with self.price_lock:
            if symbol in self.prices:
                price_data = self.prices[symbol]
                # Check if price is recent (< 5 seconds old)
                if (datetime.now() - price_data['timestamp']).total_seconds() < 5:
                    return price_data['price']
        
        # Fallback to REST API
        return self._get_price_rest(symbol)
    
    def _get_price_rest(self, symbol: str) -> Optional[float]:
        """Get price via REST API"""
        if not self._check_rate_limit():
            return None
        
        try:
            response = requests.get(
                f"{self.REST_BASE_URL}/ticker/price",
                params={'symbol': symbol},
                timeout=5
            )
            
            self._record_request()
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                
                # Update cache
                with self.price_lock:
                    self.prices[symbol] = {
                        'price': price,
                        'timestamp': datetime.now()
                    }
                
                return price
            
        except Exception as e:
            print(f"REST API error for {symbol}: {e}")
        
        return None
    
    def get_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Get prices for multiple symbols
        
        Args:
            symbols: List of trading pairs, or None for all tracked symbols
        
        Returns:
            Dictionary mapping symbol to price
        """
        symbols_to_fetch = symbols or self.symbols
        prices = {}
        
        for symbol in symbols_to_fetch:
            price = self.get_price(symbol)
            if price is not None:
                prices[symbol] = price
        
        return prices
    
    def get_24h_stats(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get 24-hour statistics for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
        
        Returns:
            Dictionary with 24h stats or None
        """
        # Try cache first
        with self.price_lock:
            if symbol in self.prices and 'volume_24h' in self.prices[symbol]:
                return self.prices[symbol]
        
        # Fetch from REST API
        if not self._check_rate_limit():
            return None
        
        try:
            response = requests.get(
                f"{self.REST_BASE_URL}/ticker/24hr",
                params={'symbol': symbol},
                timeout=5
            )
            
            self._record_request()
            
            if response.status_code == 200:
                data = response.json()
                stats = {
                    'price': float(data['lastPrice']),
                    'timestamp': datetime.now(),
                    'volume_24h': float(data['volume']),
                    'price_change_24h': float(data['priceChange']),
                    'price_change_pct_24h': float(data['priceChangePercent']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice'])
                }
                
                # Update cache
                with self.price_lock:
                    self.prices[symbol] = stats
                
                return stats
        
        except Exception as e:
            print(f"24h stats error for {symbol}: {e}")
        
        return None
    
    def get_historical_klines(
        self,
        symbol: str,
        interval: str = '1h',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical candlestick data (OHLCV)
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Time interval ('1m', '5m', '15m', '1h', '4h', '1d', etc.)
            limit: Number of candles to fetch (max 1000)
        
        Returns:
            List of candlestick dictionaries
        """
        if not self._check_rate_limit():
            return []
        
        try:
            response = requests.get(
                f"{self.REST_BASE_URL}/klines",
                params={
                    'symbol': symbol,
                    'interval': interval,
                    'limit': min(limit, 1000)
                },
                timeout=10
            )
            
            self._record_request()
            
            if response.status_code == 200:
                klines = []
                for k in response.json():
                    klines.append({
                        'timestamp': datetime.fromtimestamp(k[0] / 1000),
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5])
                    })
                return klines
        
        except Exception as e:
            print(f"Historical data error for {symbol}: {e}")
        
        return []
    
    def _check_rate_limit(self) -> bool:
        """Check if we can make a request without exceeding rate limit"""
        self._clean_old_requests()
        return len(self.request_times) < self.MAX_REQUESTS_PER_MINUTE
    
    def _record_request(self) -> None:
        """Record that a request was made"""
        self.request_times.append(datetime.now())
        self._clean_old_requests()
    
    def _clean_old_requests(self) -> None:
        """Remove requests older than 1 minute"""
        cutoff = datetime.now() - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get WebSocket connection status"""
        return {
            'connected': self.ws_connection is not None,
            'running': self.ws_running,
            'symbols': len(self.symbols),
            'cached_prices': len(self.prices),
            'last_update': self.last_update,
            'connection_errors': self.connection_errors,
            'rate_limit_used': len(self.request_times),
            'rate_limit_max': self.MAX_REQUESTS_PER_MINUTE
        }
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        if self.ws_running and self.ws_connection is None:
            return False
        
        if self.last_update is not None:
            # Check if we've received updates recently (within 60 seconds)
            seconds_since_update = (datetime.now() - self.last_update).total_seconds()
            if seconds_since_update > 60:
                return False
        
        return True
