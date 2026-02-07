"""
Price Aggregator - Multi-Source Price Feeds with Automatic Fallbacks

Aggregates prices from multiple sources with intelligent fallback logic:
1. Primary: Binance WebSocket (real-time, <100ms)
2. Fallback 1: Binance REST API
3. Fallback 2: CoinGecko API

Ensures maximum uptime and reliability.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import time

from .binance_client import BinanceClient
from .coingecko_client import CoinGeckoClient


class PriceAggregator:
    """Multi-source price aggregator with intelligent fallbacks"""
    
    # Symbol mapping between different exchanges
    SYMBOL_MAPPINGS = {
        'BTC': {'binance': 'BTCUSDT', 'coingecko': 'bitcoin'},
        'ETH': {'binance': 'ETHUSDT', 'coingecko': 'ethereum'},
        'BNB': {'binance': 'BNBUSDT', 'coingecko': 'binancecoin'},
        'SOL': {'binance': 'SOLUSDT', 'coingecko': 'solana'},
        'XRP': {'binance': 'XRPUSDT', 'coingecko': 'ripple'},
        'ADA': {'binance': 'ADAUSDT', 'coingecko': 'cardano'},
        'AVAX': {'binance': 'AVAXUSDT', 'coingecko': 'avalanche-2'},
        'DOGE': {'binance': 'DOGEUSDT', 'coingecko': 'dogecoin'},
        'MATIC': {'binance': 'MATICUSDT', 'coingecko': 'matic-network'},
        'DOT': {'binance': 'DOTUSDT', 'coingecko': 'polkadot'},
        'UNI': {'binance': 'UNIUSDT', 'coingecko': 'uniswap'},
        'LINK': {'binance': 'LINKUSDT', 'coingecko': 'chainlink'},
    }
    
    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        enable_websocket: bool = True,
        websocket_callback: Optional[Callable] = None
    ):
        """
        Initialize price aggregator
        
        Args:
            symbols: List of symbols to track (e.g., ['BTC', 'ETH'])
            enable_websocket: Whether to start WebSocket connection
            websocket_callback: Optional callback for WebSocket price updates
        """
        self.symbols = symbols or ['BTC', 'ETH', 'BNB', 'SOL']
        
        # Initialize data sources
        binance_symbols = [self._get_binance_symbol(s) for s in self.symbols]
        self.binance = BinanceClient(symbols=binance_symbols)
        self.coingecko = CoinGeckoClient()
        
        # Start WebSocket if enabled
        if enable_websocket:
            self.binance.start_websocket(callback=websocket_callback)
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'binance_rest_hits': 0,  # Renamed from binance_ws_hits for clarity
            'coingecko_hits': 0,
            'failures': 0
        }
    
    def get_price(self, symbol: str, source: Optional[str] = None) -> Optional[float]:
        """
        Get current price for a symbol with automatic fallbacks
        
        Args:
            symbol: Symbol to get price for (e.g., 'BTC', 'ETH')
            source: Optional specific source ('binance', 'coingecko', or None for auto)
        
        Returns:
            Current price or None if all sources fail
        """
        self.stats['total_requests'] += 1
        
        # If source is specified, use only that source
        if source == 'coingecko':
            return self._get_price_coingecko(symbol)
        elif source == 'binance':
            return self._get_price_binance(symbol)
        
        # Auto-fallback logic
        # 1. Try Binance (WebSocket cache or REST)
        price = self._get_price_binance(symbol)
        if price is not None:
            self.stats['binance_rest_hits'] += 1  # Track as Binance hit (WS or REST)
            return price
        
        # 2. Fallback to CoinGecko
        price = self._get_price_coingecko(symbol)
        if price is not None:
            self.stats['coingecko_hits'] += 1
            return price
        
        # All sources failed
        self.stats['failures'] += 1
        return None
    
    def get_prices(
        self,
        symbols: Optional[List[str]] = None,
        source: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get prices for multiple symbols
        
        Args:
            symbols: List of symbols, or None for all tracked symbols
            source: Optional specific source
        
        Returns:
            Dictionary mapping symbol to price
        """
        symbols_to_fetch = symbols or self.symbols
        prices = {}
        
        for symbol in symbols_to_fetch:
            price = self.get_price(symbol, source=source)
            if price is not None:
                prices[symbol] = price
        
        return prices
    
    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed market data (24h stats, volume, etc.)
        
        Args:
            symbol: Symbol to get data for
        
        Returns:
            Dictionary with market data or None
        """
        # Try Binance first (faster)
        binance_symbol = self._get_binance_symbol(symbol)
        stats = self.binance.get_24h_stats(binance_symbol)
        
        if stats:
            return {
                'symbol': symbol,
                'price': stats['price'],
                'volume_24h': stats.get('volume_24h'),
                'price_change_24h': stats.get('price_change_24h'),
                'price_change_pct_24h': stats.get('price_change_pct_24h'),
                'high_24h': stats.get('high_24h'),
                'low_24h': stats.get('low_24h'),
                'source': 'binance',
                'timestamp': stats['timestamp']
            }
        
        # Fallback to CoinGecko
        coingecko_id = self._get_coingecko_id(symbol)
        market_data = self.coingecko.get_market_data(coingecko_id)
        
        if market_data:
            return {
                'symbol': symbol,
                'price': market_data['price_usd'],
                'volume_24h': market_data.get('volume_24h_usd'),
                'price_change_24h': market_data.get('price_change_24h'),
                'price_change_pct_24h': market_data.get('price_change_pct_24h'),
                'high_24h': market_data.get('high_24h'),
                'low_24h': market_data.get('low_24h'),
                'market_cap': market_data.get('market_cap_usd'),
                'source': 'coingecko',
                'timestamp': datetime.now()
            }
        
        return None
    
    def get_historical_prices(
        self,
        symbol: str,
        days: int = 7,
        interval: str = '1h'
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data
        
        Args:
            symbol: Symbol to get data for
            days: Number of days of history
            interval: Time interval ('1m', '5m', '1h', '1d', etc.)
        
        Returns:
            List of historical price data points
        """
        # Try Binance first (more granular intervals)
        if days <= 30:  # Binance is better for short-term data
            binance_symbol = self._get_binance_symbol(symbol)
            
            # Calculate limit based on days and interval
            intervals_per_day = {
                '1m': 1440, '5m': 288, '15m': 96, '30m': 48,
                '1h': 24, '4h': 6, '1d': 1
            }
            limit = intervals_per_day.get(interval, 24) * days
            
            klines = self.binance.get_historical_klines(
                binance_symbol,
                interval=interval,
                limit=min(limit, 1000)
            )
            
            if klines:
                return [
                    {
                        'symbol': symbol,
                        'timestamp': k['timestamp'],
                        'open': k['open'],
                        'high': k['high'],
                        'low': k['low'],
                        'close': k['close'],
                        'volume': k['volume']
                    }
                    for k in klines
                ]
        
        # Fallback to CoinGecko (better for longer timeframes)
        coingecko_id = self._get_coingecko_id(symbol)
        prices = self.coingecko.get_historical_prices(
            coingecko_id,
            days=days
        )
        
        return [
            {
                'symbol': symbol,
                'timestamp': p['timestamp'],
                'price': p['price']
            }
            for p in prices
        ]
    
    def _get_price_binance(self, symbol: str) -> Optional[float]:
        """Get price from Binance"""
        binance_symbol = self._get_binance_symbol(symbol)
        return self.binance.get_price(binance_symbol)
    
    def _get_price_coingecko(self, symbol: str) -> Optional[float]:
        """Get price from CoinGecko"""
        coingecko_id = self._get_coingecko_id(symbol)
        return self.coingecko.get_price(coingecko_id)
    
    def _get_binance_symbol(self, symbol: str) -> str:
        """Convert generic symbol to Binance trading pair"""
        # Remove common suffixes
        symbol = symbol.upper().replace('USDT', '').replace('USD', '')
        
        # Use mapping if available
        if symbol in self.SYMBOL_MAPPINGS:
            return self.SYMBOL_MAPPINGS[symbol]['binance']
        
        # Default: add USDT suffix
        return f"{symbol}USDT"
    
    def _get_coingecko_id(self, symbol: str) -> str:
        """Convert generic symbol to CoinGecko coin ID"""
        symbol = symbol.upper().replace('USDT', '').replace('USD', '')
        
        # Use mapping if available
        if symbol in self.SYMBOL_MAPPINGS:
            return self.SYMBOL_MAPPINGS[symbol]['coingecko']
        
        # Default: lowercase symbol
        return symbol.lower()
    
    def add_symbol(self, symbol: str) -> None:
        """
        Add a new symbol to track
        
        Args:
            symbol: Symbol to add (e.g., 'BTC', 'ETH')
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            
            # Add to Binance if WebSocket is running
            binance_symbol = self._get_binance_symbol(symbol)
            if binance_symbol not in self.binance.symbols:
                self.binance.symbols.append(binance_symbol)
    
    def remove_symbol(self, symbol: str) -> None:
        """
        Remove a symbol from tracking
        
        Args:
            symbol: Symbol to remove
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all data sources"""
        binance_status = self.binance.get_connection_status()
        coingecko_status = self.coingecko.get_rate_limit_status()
        
        return {
            'binance': {
                'connected': binance_status['connected'],
                'healthy': self.binance.is_healthy(),
                'symbols': binance_status['symbols'],
                'cached_prices': binance_status['cached_prices'],
                'rate_limit_used': binance_status['rate_limit_used'],
                'rate_limit_max': binance_status['rate_limit_max']
            },
            'coingecko': {
                'rate_limit_used': coingecko_status['requests_used'],
                'rate_limit_max': coingecko_status['max_per_minute'],
                'cached_prices': coingecko_status['cached_prices']
            },
            'aggregator': {
                'symbols': len(self.symbols),
                'total_requests': self.stats['total_requests'],
                'binance_hits': self.stats['binance_rest_hits'],  # Renamed from binance_ws_hits
                'coingecko_hits': self.stats['coingecko_hits'],
                'failures': self.stats['failures'],
                'success_rate': (
                    (self.stats['total_requests'] - self.stats['failures']) /
                    self.stats['total_requests'] * 100
                    if self.stats['total_requests'] > 0 else 0
                )
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown all connections"""
        self.binance.stop_websocket()
