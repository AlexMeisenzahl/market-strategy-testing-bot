"""
Crypto Price Manager - Unified price management service

Coordinates all crypto price sources (CoinGecko, Binance, Coinbase) and provides:
- Multi-source price aggregation with median calculation
- Discrepancy detection and warning
- Historical price tracking via CSV logging
- Caching for performance
- Thread-safe parallel fetching from multiple sources
"""

import csv
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apis.coingecko_client import CoinGeckoClient
from apis.binance_client import BinanceClient
from exchanges.coinbase_client import CoinbaseClient


class CryptoPriceManager:
    """
    Central manager for all cryptocurrency price data
    
    Features:
    - Aggregates prices from multiple sources in parallel
    - Uses median price (resistant to outliers)
    - Detects and warns on discrepancies >5%
    - Stores historical prices in CSV
    - Provides price history queries
    - Configurable caching
    """
    
    def __init__(self, logger=None, log_dir: str = "logs", config: Dict = None):
        """
        Initialize crypto price manager
        
        Args:
            logger: Logger instance
            log_dir: Directory for price history logs
            config: Configuration dictionary
        """
        self.logger = logger
        self.log_dir = Path(log_dir)
        self.config = config or {}
        
        # Initialize API clients
        crypto_config = self.config.get('crypto_apis', {})
        
        self.coingecko = CoinGeckoClient(logger=logger) if crypto_config.get('coingecko', {}).get('enabled', True) else None
        self.binance = BinanceClient(logger=logger) if crypto_config.get('binance', {}).get('enabled', True) else None
        self.coinbase = CoinbaseClient(logger=logger) if crypto_config.get('coinbase', {}).get('enabled', True) else None
        
        # Caching
        self.cache = {}
        self.cache_duration = 30  # seconds
        
        # Configuration
        self.discrepancy_threshold = 0.05  # 5% discrepancy warning threshold
        self.min_sources = 1  # Minimum sources required
        
        # Ensure logs directory exists
        self._ensure_log_directory()
        self._initialize_price_history_csv()
        
    def _ensure_log_directory(self) -> None:
        """Create logs directory if it doesn't exist"""
        self.log_dir.mkdir(exist_ok=True)
    
    def _initialize_price_history_csv(self) -> None:
        """Initialize crypto price history CSV file"""
        history_file = self.log_dir / "crypto_price_history.csv"
        if not history_file.exists():
            with open(history_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'symbol', 'price_usd', 'sources_count',
                    'discrepancy_pct', 'source_list', 'price_min', 'price_max'
                ])
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get current prices for multiple symbols from all sources
        
        Args:
            symbols: List of crypto symbols (e.g., ['BTC', 'ETH', 'SOL'])
            
        Returns:
            Dictionary mapping symbols to price data with metadata
            
        Example:
            >>> manager = CryptoPriceManager(logger=logger)
            >>> prices = manager.get_current_prices(['BTC', 'ETH'])
            >>> print(f"BTC: ${prices['BTC']['price_usd']}")
        """
        results = {}
        
        for symbol in symbols:
            # Check cache first
            cache_key = f"price_{symbol}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if time.time() - cached_time < self.cache_duration:
                    results[symbol] = cached_data
                    continue
            
            # Fetch from all sources in parallel
            price_data = self._fetch_price_from_all_sources(symbol)
            
            if price_data:
                # Cache the result
                self.cache[cache_key] = (price_data, time.time())
                results[symbol] = price_data
                
                # Store in history
                self._store_price_history(symbol, price_data)
        
        return results
    
    def _fetch_price_from_all_sources(self, symbol: str) -> Optional[Dict]:
        """
        Fetch price from all enabled sources in parallel
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            Aggregated price data or None
        """
        prices = {}
        
        # Use ThreadPoolExecutor for parallel fetching
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            # Submit tasks for each enabled source
            if self.coingecko:
                futures['coingecko'] = executor.submit(self._fetch_from_coingecko, symbol)
            if self.binance:
                futures['binance'] = executor.submit(self._fetch_from_binance, symbol)
            if self.coinbase:
                futures['coinbase'] = executor.submit(self._fetch_from_coinbase, symbol)
            
            # Collect results
            for source, future in futures.items():
                try:
                    price = future.result(timeout=10)
                    if price:
                        prices[source] = float(price)
                except Exception as e:
                    if self.logger:
                        self.logger.log_warning(f"Failed to fetch from {source}: {str(e)}")
        
        # Check if we have enough data
        if len(prices) < self.min_sources:
            if self.logger:
                self.logger.log_error(f"Insufficient price sources for {symbol}: only {len(prices)} available")
            return None
        
        # Calculate aggregated price
        return self._aggregate_prices(symbol, prices)
    
    def _fetch_from_coingecko(self, symbol: str) -> Optional[Decimal]:
        """Fetch price from CoinGecko"""
        try:
            price = self.coingecko.get_price(symbol)
            return Decimal(str(price)) if price else None
        except:
            return None
    
    def _fetch_from_binance(self, symbol: str) -> Optional[Decimal]:
        """Fetch price from Binance"""
        try:
            binance_symbol = f"{symbol}USDT"
            price = self.binance.get_price(binance_symbol)
            return Decimal(str(price)) if price else None
        except:
            return None
    
    def _fetch_from_coinbase(self, symbol: str) -> Optional[Decimal]:
        """Fetch price from Coinbase"""
        try:
            price = self.coinbase.get_price(symbol)
            return price if price else None
        except:
            return None
    
    def _aggregate_prices(self, symbol: str, prices: Dict[str, float]) -> Dict:
        """
        Aggregate prices from multiple sources
        
        Args:
            symbol: Crypto symbol
            prices: Dictionary of source -> price
            
        Returns:
            Aggregated price data with metadata
        """
        if not prices:
            return None
        
        price_values = list(prices.values())
        
        # Calculate median price
        median_price = Decimal(str(statistics.median(price_values)))
        
        # Calculate price range and discrepancy
        min_price = min(price_values)
        max_price = max(price_values)
        price_range = max_price - min_price
        discrepancy_pct = (price_range / float(median_price)) * 100 if median_price > 0 else 0
        
        # Warn if discrepancy is high
        if discrepancy_pct > self.discrepancy_threshold * 100:
            if self.logger:
                self.logger.log_warning(
                    f"High price discrepancy for {symbol}: {discrepancy_pct:.2f}% "
                    f"(${min_price:.2f} - ${max_price:.2f})"
                )
        
        # Calculate 24h change from historical data if available
        # TODO: Implement proper 24h change calculation by fetching historical price data
        # from the price APIs or database. For now, returning 0 as placeholder.
        change_24h_pct = 0.0
        
        return {
            'symbol': symbol,
            'name': self._get_crypto_name(symbol),
            'price_usd': median_price,
            'change_24h_pct': change_24h_pct,
            'sources': list(prices.keys()),
            'sources_count': len(prices),
            'price_min': Decimal(str(min_price)),
            'price_max': Decimal(str(max_price)),
            'discrepancy_pct': Decimal(str(discrepancy_pct)),
            'last_updated': datetime.now().isoformat(),
            'source': 'Aggregated'
        }
    
    def _get_crypto_name(self, symbol: str) -> str:
        """Get full name for crypto symbol"""
        names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'SOL': 'Solana',
            'XRP': 'XRP',
            'ADA': 'Cardano',
            'DOT': 'Polkadot',
            'AVAX': 'Avalanche',
            'MATIC': 'Polygon',
            'DOGE': 'Dogecoin',
            'LTC': 'Litecoin',
        }
        return names.get(symbol, symbol)
    
    def _store_price_history(self, symbol: str, price_data: Dict) -> None:
        """Store price in historical CSV log"""
        try:
            history_file = self.log_dir / "crypto_price_history.csv"
            with open(history_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    symbol,
                    str(price_data['price_usd']),
                    price_data['sources_count'],
                    str(price_data['discrepancy_pct']),
                    ','.join(price_data['sources']),
                    str(price_data.get('price_min', '')),
                    str(price_data.get('price_max', ''))
                ])
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to store price history: {str(e)}")
    
    def get_price_history(self, symbol: str, hours: int = 24) -> List[Dict]:
        """
        Get historical prices for a symbol from CSV log
        
        Args:
            symbol: Crypto symbol
            hours: Number of hours of history to retrieve
            
        Returns:
            List of historical price records
        """
        history_file = self.log_dir / "crypto_price_history.csv"
        
        if not history_file.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = []
        
        try:
            with open(history_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['symbol'] == symbol:
                        timestamp = datetime.fromisoformat(row['timestamp'])
                        if timestamp >= cutoff_time:
                            history.append({
                                'timestamp': row['timestamp'],
                                'price_usd': Decimal(row['price_usd']),
                                'sources_count': int(row['sources_count']),
                                'discrepancy_pct': Decimal(row.get('discrepancy_pct', '0'))
                            })
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Failed to read price history: {str(e)}")
        
        return history
    
    def check_price_alert(self, symbol: str, threshold: Decimal, direction: str) -> bool:
        """
        Check if price has crossed a threshold
        
        Args:
            symbol: Crypto symbol
            threshold: Price threshold
            direction: 'above' or 'below'
            
        Returns:
            True if alert condition is met
        """
        prices = self.get_current_prices([symbol])
        
        if symbol not in prices:
            return False
        
        current_price = prices[symbol]['price_usd']
        
        if direction == 'above':
            return current_price > threshold
        elif direction == 'below':
            return current_price < threshold
        
        return False
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all price sources
        
        Returns:
            Dictionary mapping source names to health status
        """
        health = {}
        
        if self.coingecko:
            health['coingecko'] = self.coingecko.health_check()
        if self.binance:
            health['binance'] = self.binance.health_check()
        if self.coinbase:
            health['coinbase'] = self.coinbase.health_check()
        
        healthy_count = sum(1 for v in health.values() if v)
        total_count = len(health)
        
        if self.logger:
            self.logger.log_info(f"Price sources health: {healthy_count}/{total_count} healthy")
        
        return health
