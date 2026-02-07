"""
Binance WebSocket + REST API Client
- Real-time price streams
- Historical OHLCV data
- 1200 requests/minute (FREE)
"""

import asyncio
import json
import requests
import time
from typing import Dict, Optional, List, Callable
from datetime import datetime


class BinanceClient:
    """Client for Binance WebSocket and REST API"""
    
    def __init__(self):
        """Initialize Binance client"""
        self.ws_base = "wss://stream.binance.com:9443"
        self.rest_base = "https://api.binance.com/api/v3"
        
        # Price cache for WebSocket streams
        self.price_cache = {}
        self.callbacks = {}
        self.ws_tasks = []
        
    def get_current_price(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """
        Get current price via REST API (fallback)
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Current price as float, or None on error
        """
        try:
            url = f"{self.rest_base}/ticker/price"
            params = {'symbol': symbol.upper()}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return float(data['price'])
            
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_24h_ticker(self, symbol: str = 'BTCUSDT') -> Optional[Dict]:
        """
        Get 24-hour ticker statistics
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with 24h stats, or None on error
        """
        try:
            url = f"{self.rest_base}/ticker/24hr"
            params = {'symbol': symbol.upper()}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return {
                'symbol': data['symbol'],
                'price': float(data['lastPrice']),
                'volume': float(data['volume']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'price_change_percent': float(data['priceChangePercent'])
            }
            
        except Exception as e:
            print(f"Error fetching 24h ticker for {symbol}: {e}")
            return None
    
    def get_historical_klines(self, symbol: str = 'BTCUSDT', 
                             interval: str = '1h', limit: int = 100) -> Optional[List[Dict]]:
        """
        Get historical candlestick data
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of klines to return (max 1000)
            
        Returns:
            List of kline dictionaries, or None on error
        """
        try:
            url = f"{self.rest_base}/klines"
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'limit': min(limit, 1000)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse klines into readable format
            klines = []
            for k in data:
                klines.append({
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': k[6],
                    'quote_volume': float(k[7]),
                    'trades': k[8]
                })
            
            return klines
            
        except Exception as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return None
    
    async def stream_price(self, symbol: str = 'BTCUSDT', 
                          callback: Optional[Callable] = None) -> None:
        """
        WebSocket real-time price stream
        
        Args:
            symbol: Trading pair symbol
            callback: Function to call with price updates
        """
        try:
            import websockets
            
            symbol_lower = symbol.lower()
            uri = f"{self.ws_base}/ws/{symbol_lower}@ticker"
            
            async with websockets.connect(uri) as websocket:
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    
                    # Parse ticker data
                    price_data = {
                        'symbol': data['s'],
                        'price': float(data['c']),
                        'volume': float(data['v']),
                        'high': float(data['h']),
                        'low': float(data['l']),
                        'timestamp': data['E']
                    }
                    
                    # Update cache
                    self.price_cache[symbol.upper()] = price_data
                    
                    # Call callback if provided
                    if callback:
                        callback(price_data)
                        
        except Exception as e:
            print(f"WebSocket error for {symbol}: {e}")
    
    async def stream_multiple_prices(self, symbols: List[str], 
                                     callback: Optional[Callable] = None) -> None:
        """
        Stream prices for multiple symbols concurrently
        
        Args:
            symbols: List of trading pair symbols
            callback: Function to call with price updates
        """
        tasks = [self.stream_price(symbol, callback) for symbol in symbols]
        await asyncio.gather(*tasks)
    
    def start_stream(self, symbols: List[str], 
                    callback: Optional[Callable] = None) -> None:
        """
        Start WebSocket streams in background (non-blocking)
        
        Args:
            symbols: List of trading pair symbols to stream
            callback: Function to call with price updates
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create task for streaming
        task = loop.create_task(self.stream_multiple_prices(symbols, callback))
        self.ws_tasks.append(task)
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=loop.run_forever, daemon=True)
        thread.start()
    
    def get_cached_price(self, symbol: str) -> Optional[Dict]:
        """
        Get most recent price from WebSocket cache
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Cached price data, or None if not available
        """
        return self.price_cache.get(symbol.upper())
    
    def stop_streams(self) -> None:
        """Stop all WebSocket streams"""
        for task in self.ws_tasks:
            task.cancel()
        self.ws_tasks.clear()
