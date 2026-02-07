"""
Price Aggregator
Aggregates prices from multiple sources with fallbacks
- Primary: Binance WebSocket
- Fallback 1: Binance REST
- Fallback 2: CoinGecko
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time

from .binance_client import BinanceClient
from .coingecko_client import CoinGeckoClient


class PriceAggregator:
    """Aggregates cryptocurrency prices from multiple sources with intelligent fallback"""
    
    def __init__(self, enable_websocket: bool = True):
        """
        Initialize price aggregator
        
        Args:
            enable_websocket: Whether to enable WebSocket streaming (default: True)
        """
        self.binance = BinanceClient()
        self.coingecko = CoinGeckoClient()
        
        self.enable_websocket = enable_websocket
        self.websocket_started = False
        
        # Cache for fallback
        self.price_cache = {}
        self.cache_expiry = {}
        self.cache_ttl = 60  # Cache prices for 60 seconds
        
        # Source priority
        self.sources = ['binance_ws', 'binance_rest', 'coingecko']
        
        # Statistics
        self.stats = {
            'binance_ws': {'success': 0, 'failure': 0},
            'binance_rest': {'success': 0, 'failure': 0},
            'coingecko': {'success': 0, 'failure': 0}
        }
    
    def start_websocket_streams(self, symbols: List[str]) -> None:
        """
        Start WebSocket streams for specified symbols
        
        Args:
            symbols: List of trading pair symbols to stream
        """
        if not self.enable_websocket:
            return
        
        if not self.websocket_started:
            self.binance.start_stream(symbols, self._websocket_callback)
            self.websocket_started = True
    
    def _websocket_callback(self, price_data: Dict) -> None:
        """
        Callback for WebSocket price updates
        
        Args:
            price_data: Price data from WebSocket
        """
        symbol = price_data.get('symbol')
        if symbol:
            self.price_cache[symbol] = price_data
            self.cache_expiry[symbol] = datetime.now() + timedelta(seconds=self.cache_ttl)
    
    def get_best_price(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """
        Get best available price from sources in priority order
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Current price, or None if all sources fail
        """
        for source in self.sources:
            price = None
            
            if source == 'binance_ws' and self.enable_websocket:
                price = self._get_from_websocket(symbol)
            elif source == 'binance_rest':
                price = self._get_from_binance_rest(symbol)
            elif source == 'coingecko':
                price = self._get_from_coingecko(symbol)
            
            if price is not None:
                self.stats[source]['success'] += 1
                self._update_cache(symbol, price)
                return price
            else:
                self.stats[source]['failure'] += 1
        
        # All sources failed, try cache
        cached = self._get_from_cache(symbol)
        if cached:
            return cached
        
        return None
    
    def get_best_market_data(self, symbol: str = 'BTCUSDT') -> Optional[Dict]:
        """
        Get comprehensive market data from best available source
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Market data dictionary, or None if unavailable
        """
        # Try Binance 24h ticker first
        if self.enable_websocket:
            cached = self.binance.get_cached_price(symbol)
            if cached and self._is_cache_valid(symbol):
                return cached
        
        # Try Binance REST
        ticker = self.binance.get_24h_ticker(symbol)
        if ticker:
            return ticker
        
        # Try CoinGecko as fallback
        market_data = self.coingecko.get_market_data(symbol)
        if market_data:
            return market_data
        
        return None
    
    def get_prices_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple symbols efficiently
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary mapping symbols to prices
        """
        prices = {}
        
        # Try WebSocket cache first for all symbols
        if self.enable_websocket:
            for symbol in symbols:
                ws_price = self._get_from_websocket(symbol)
                if ws_price:
                    prices[symbol] = ws_price
        
        # Get remaining symbols from REST APIs
        remaining_symbols = [s for s in symbols if s not in prices]
        
        if remaining_symbols:
            # Try CoinGecko batch API (more efficient)
            coingecko_prices = self.coingecko.get_prices_batch(remaining_symbols)
            prices.update(coingecko_prices)
            
            # Fill in any missing with Binance REST
            still_remaining = [s for s in remaining_symbols if s not in prices]
            for symbol in still_remaining:
                binance_price = self.binance.get_current_price(symbol)
                if binance_price:
                    prices[symbol] = binance_price
        
        return prices
    
    def _get_from_websocket(self, symbol: str) -> Optional[float]:
        """Get price from WebSocket cache"""
        if not self.enable_websocket or not self.websocket_started:
            return None
        
        cached = self.binance.get_cached_price(symbol)
        if cached and self._is_cache_valid(symbol):
            return cached.get('price')
        
        return None
    
    def _get_from_binance_rest(self, symbol: str) -> Optional[float]:
        """Get price from Binance REST API"""
        try:
            return self.binance.get_current_price(symbol)
        except Exception as e:
            print(f"Binance REST error for {symbol}: {e}")
            return None
    
    def _get_from_coingecko(self, symbol: str) -> Optional[float]:
        """Get price from CoinGecko API"""
        try:
            return self.coingecko.get_price(symbol)
        except Exception as e:
            print(f"CoinGecko error for {symbol}: {e}")
            return None
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached price is still valid"""
        if symbol not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[symbol]
    
    def _get_from_cache(self, symbol: str) -> Optional[float]:
        """Get price from fallback cache"""
        if symbol in self.price_cache and self._is_cache_valid(symbol):
            data = self.price_cache[symbol]
            if isinstance(data, dict):
                return data.get('price')
            elif isinstance(data, (int, float)):
                return float(data)
        return None
    
    def _update_cache(self, symbol: str, price: float) -> None:
        """Update price cache"""
        self.price_cache[symbol] = {
            'symbol': symbol,
            'price': price,
            'timestamp': datetime.now().isoformat()
        }
        self.cache_expiry[symbol] = datetime.now() + timedelta(seconds=self.cache_ttl)
    
    def get_statistics(self) -> Dict:
        """
        Get usage statistics for all sources
        
        Returns:
            Dictionary with source statistics
        """
        total_requests = sum(
            self.stats[source]['success'] + self.stats[source]['failure']
            for source in self.sources
        )
        
        stats = {
            'total_requests': total_requests,
            'sources': {}
        }
        
        for source in self.sources:
            success = self.stats[source]['success']
            failure = self.stats[source]['failure']
            total = success + failure
            
            stats['sources'][source] = {
                'success': success,
                'failure': failure,
                'total': total,
                'success_rate': (success / total * 100) if total > 0 else 0
            }
        
        return stats
    
    def stop(self) -> None:
        """Stop all data sources"""
        if self.websocket_started:
            self.binance.stop_streams()
            self.websocket_started = False
