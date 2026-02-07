"""
Free Data Aggregator
Combines multiple free data sources with intelligent fallback logic
No API keys required
"""

import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from .binance_client import BinanceClient
from .coingecko_client import CoinGeckoClient
from .polymarket_subgraph import PolymarketSubgraph


class FreeDataAggregator:
    """
    Aggregates data from multiple free sources with fallback logic
    Provides unified interface for crypto and prediction market data
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize data aggregator with all free API clients
        
        Args:
            config: Optional configuration dictionary
        """
        config = config or {}
        
        # Initialize all free API clients
        binance_config = config.get('binance', {})
        self.binance = BinanceClient(
            rate_limit_per_minute=binance_config.get('rate_limit_per_minute', 1200)
        )
        
        coingecko_config = config.get('coingecko', {})
        self.coingecko = CoinGeckoClient(
            rate_limit_per_minute=coingecko_config.get('rate_limit_per_minute', 50)
        )
        
        polymarket_config = config.get('polymarket_subgraph', {})
        self.polymarket = PolymarketSubgraph(
            query_timeout_seconds=polymarket_config.get('query_timeout_seconds', 10)
        )
        
        # Cache for reducing API calls
        self.cache = {}
        self.cache_ttl = config.get('cache_ttl_seconds', 10)  # Default 10 second cache
        
        # Track which sources are healthy
        self.source_health = {
            'binance': True,
            'coingecko': True,
            'polymarket': True
        }
        
        # Last health check time
        self.last_health_check = datetime.now()
        self.health_check_interval = timedelta(minutes=5)
    
    def _get_cache_key(self, key_type: str, identifier: str) -> str:
        """Generate cache key"""
        return f"{key_type}:{identifier.upper()}"
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get data from cache if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            age = (datetime.now() - timestamp).total_seconds()
            
            if age < self.cache_ttl:
                return data
        
        return None
    
    def _set_cache(self, key: str, data: Dict) -> None:
        """Store data in cache"""
        self.cache[key] = (data, datetime.now())
    
    def _check_source_health(self) -> None:
        """Periodically check health of all data sources"""
        now = datetime.now()
        
        if now - self.last_health_check < self.health_check_interval:
            return
        
        self.source_health['binance'] = self.binance.ping()
        self.source_health['coingecko'] = self.coingecko.ping()
        self.source_health['polymarket'] = self.polymarket.ping()
        
        self.last_health_check = now
    
    def get_crypto_price(self, symbol: str) -> Optional[float]:
        """
        Get crypto price with fallback logic: Binance → CoinGecko
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Current price or None if all sources fail
        """
        # Check cache first
        cache_key = self._get_cache_key('crypto_price', symbol)
        cached = self._get_cached(cache_key)
        if cached:
            return cached.get('price')
        
        # Check source health
        self._check_source_health()
        
        price = None
        
        # Try Binance first (1200 req/min, faster)
        if self.source_health['binance']:
            price = self.binance.get_price(symbol)
        
        # Fallback to CoinGecko if Binance fails
        if price is None and self.source_health['coingecko']:
            price = self.coingecko.get_price(symbol)
        
        # Cache the result
        if price is not None:
            self._set_cache(cache_key, {'price': price, 'timestamp': datetime.now().isoformat()})
        
        return price
    
    def get_crypto_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Get comprehensive crypto market data (price, volume, 24h changes)
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Market data dictionary or None on error
        """
        # Check cache first
        cache_key = self._get_cache_key('crypto_market', symbol)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # Check source health
        self._check_source_health()
        
        data = None
        
        # Try Binance first (has 24h ticker data)
        if self.source_health['binance']:
            data = self.binance.get_ticker_24h(symbol)
        
        # Fallback to CoinGecko (has more comprehensive data)
        if data is None and self.source_health['coingecko']:
            data = self.coingecko.get_market_data(symbol)
        
        # Cache the result
        if data is not None:
            self._set_cache(cache_key, data)
        
        return data
    
    def get_multiple_crypto_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies efficiently
        
        Args:
            symbols: List of crypto symbols
            
        Returns:
            Dictionary mapping symbols to prices
        """
        prices = {}
        symbols_to_fetch = []
        
        # Check cache for each symbol
        for symbol in symbols:
            cache_key = self._get_cache_key('crypto_price', symbol)
            cached = self._get_cached(cache_key)
            if cached:
                prices[symbol.upper()] = cached.get('price')
            else:
                symbols_to_fetch.append(symbol)
        
        # If all symbols were cached, return
        if not symbols_to_fetch:
            return prices
        
        # Check source health
        self._check_source_health()
        
        # Try Binance first (can get all prices in one request)
        if self.source_health['binance']:
            binance_prices = self.binance.get_multiple_prices(symbols_to_fetch)
            for symbol, price in binance_prices.items():
                prices[symbol] = price
                cache_key = self._get_cache_key('crypto_price', symbol)
                self._set_cache(cache_key, {'price': price, 'timestamp': datetime.now().isoformat()})
            
            # Remove successfully fetched symbols
            symbols_to_fetch = [s for s in symbols_to_fetch if s.upper() not in binance_prices]
        
        # Fallback to CoinGecko for remaining symbols
        if symbols_to_fetch and self.source_health['coingecko']:
            coingecko_prices = self.coingecko.get_multiple_prices(symbols_to_fetch)
            for symbol, price in coingecko_prices.items():
                prices[symbol] = price
                cache_key = self._get_cache_key('crypto_price', symbol)
                self._set_cache(cache_key, {'price': price, 'timestamp': datetime.now().isoformat()})
        
        return prices
    
    def get_polymarket_odds(self, market_id: str) -> Optional[Dict]:
        """
        Get Polymarket market odds via Subgraph
        
        Args:
            market_id: Market contract address
            
        Returns:
            Dictionary with 'yes' and 'no' prices, or None on error
        """
        # Check cache first
        cache_key = self._get_cache_key('polymarket', market_id)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # Check source health
        self._check_source_health()
        
        # Get odds from Polymarket Subgraph
        if self.source_health['polymarket']:
            odds = self.polymarket.get_market_odds(market_id)
            
            if odds:
                # Cache the result
                self._set_cache(cache_key, odds)
                return odds
        
        return None
    
    def get_polymarket_active_markets(self, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get active Polymarket markets
        
        Args:
            limit: Maximum number of markets to return
            
        Returns:
            List of market dictionaries or None on error
        """
        # Check cache first
        cache_key = self._get_cache_key('polymarket_markets', f'active_{limit}')
        cached = self._get_cached(cache_key)
        if cached:
            return cached.get('markets')
        
        # Check source health
        self._check_source_health()
        
        # Get markets from Polymarket Subgraph
        if self.source_health['polymarket']:
            markets = self.polymarket.get_active_markets(limit)
            
            if markets:
                # Cache the result
                self._set_cache(cache_key, {'markets': markets})
                return markets
        
        return None
    
    def search_polymarket_markets(self, search_term: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Search Polymarket markets by question text
        
        Args:
            search_term: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching markets or None on error
        """
        # Check source health
        self._check_source_health()
        
        if self.source_health['polymarket']:
            return self.polymarket.search_markets(search_term, limit)
        
        return None
    
    def get_all_source_health(self) -> Dict[str, bool]:
        """
        Get health status of all data sources
        
        Returns:
            Dictionary mapping source names to health status
        """
        self._check_source_health()
        return self.source_health.copy()
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        now = datetime.now()
        valid_entries = 0
        expired_entries = 0
        
        for key, (data, timestamp) in self.cache.items():
            age = (now - timestamp).total_seconds()
            if age < self.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_ttl_seconds': self.cache_ttl
        }
