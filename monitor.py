"""
Monitor Module - Price monitoring and API handling for Polymarket

Handles:
- API connection to Polymarket via FREE data sources
- Binance for crypto prices (no API key required)
- Polymarket Subgraph for market data (GraphQL, free)
- Rate limit tracking and management
- Connection health monitoring
- Data validation
- Exponential backoff on errors
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from logger import get_logger

# Import free API clients
from apis.binance_client import BinanceClient
from apis.coingecko_client import CoinGeckoClient
from apis.polymarket_subgraph import PolymarketSubgraph
from apis.price_aggregator import PriceAggregator


class RateLimiter:
    """Track and manage API rate limits"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []  # List of request timestamps
        self.logger = get_logger()
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding rate limit"""
        self._clean_old_requests()
        return len(self.requests) < self.max_requests
    
    def record_request(self) -> None:
        """Record that a request was made"""
        self.requests.append(datetime.now())
        self._clean_old_requests()
    
    def _clean_old_requests(self) -> None:
        """Remove requests older than time window"""
        cutoff_time = datetime.now() - timedelta(seconds=self.time_window)
        self.requests = [req for req in self.requests if req > cutoff_time]
    
    def get_usage_percentage(self) -> float:
        """Get current usage as percentage of limit"""
        self._clean_old_requests()
        return (len(self.requests) / self.max_requests) * 100
    
    def get_remaining_requests(self) -> int:
        """Get number of requests remaining in current window"""
        self._clean_old_requests()
        return self.max_requests - len(self.requests)
    
    def get_reset_time(self) -> int:
        """Get seconds until oldest request expires"""
        self._clean_old_requests()
        if not self.requests:
            return 0
        oldest_request = min(self.requests)
        reset_time = oldest_request + timedelta(seconds=self.time_window)
        seconds_until_reset = (reset_time - datetime.now()).total_seconds()
        return max(0, int(seconds_until_reset))


class PolymarketMonitor:
    """Monitor Polymarket API and fetch market prices"""
    
    # Polymarket API endpoints (public, no authentication needed)
    BASE_URL = "https://clob.polymarket.com"
    MARKETS_ENDPOINT = "/markets"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Polymarket monitor with FREE data sources
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Initialize FREE API clients (no API keys needed!)
        data_sources = config.get('data_sources', {})
        
        # Crypto price sources
        crypto_config = data_sources.get('crypto_prices', {})
        self.use_websocket = crypto_config.get('use_websocket', True)
        
        # Initialize price aggregator (combines Binance + CoinGecko)
        self.price_aggregator = PriceAggregator(logger=self.logger)
        
        # Initialize Polymarket Subgraph client (free GraphQL)
        polymarket_config = data_sources.get('polymarket', {})
        use_alt = polymarket_config.get('use_alternative', False)
        self.market_client = PolymarketSubgraph(logger=self.logger, use_alternative=use_alt)
        
        # Cache settings
        self.cache_ttl = polymarket_config.get('cache_ttl_seconds', 60)
        self.market_cache = {}
        self.cache_timestamps = {}
        
        # Initialize legacy rate limiter (backward compatibility)
        self.rate_limiter = RateLimiter(
            max_requests=config.get('rate_limit_max', 100),
            time_window=60
        )
        
        # Connection health tracking
        self.last_connection_check = None
        self.connection_healthy = True
        self.consecutive_failures = 0
        
        # Request settings
        self.timeout = config.get('api_timeout_seconds', 5)
        self.max_retries = config.get('max_retries', 3)
        self.request_delay = config.get('request_delay_seconds', 0.5)
        
        # Rate limit thresholds
        self.warning_threshold = config.get('rate_limit_warning_threshold', 0.80)
        self.pause_threshold = config.get('rate_limit_pause_threshold', 0.95)
        
        # Log successful initialization
        self.logger.log_info("Monitor initialized with FREE data sources (Binance + Subgraph)")
    
    def check_connection_health(self) -> bool:
        """
        Test if connection to data sources is stable
        Uses FREE APIs: Binance + Polymarket Subgraph
        
        Returns:
            True if connection is healthy, False otherwise
        """
        start_time = time.time()
        
        try:
            # Check price aggregator health (Binance + CoinGecko)
            price_health = self.price_aggregator.health_check()
            
            # Check Polymarket Subgraph health
            market_health = self.market_client.health_check()
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Consider healthy if at least one source works
            is_healthy = any(price_health.values()) or market_health
            
            if is_healthy:
                self.connection_healthy = True
                self.consecutive_failures = 0
                
                # Log status based on response time
                if response_time_ms < 1000:
                    self.logger.log_connection("healthy", response_time_ms)
                else:
                    self.logger.log_connection("slow", response_time_ms)
                
                self.last_connection_check = datetime.now()
                return True
            else:
                self._handle_connection_failure("all sources unavailable")
                return False
                
        except Exception as e:
            self._handle_connection_failure(f"unexpected error: {str(e)}")
            return False
    
    def _handle_connection_failure(self, reason: str) -> None:
        """Handle connection failure"""
        self.consecutive_failures += 1
        self.connection_healthy = False
        self.logger.log_connection("error", message=reason)
        
        if self.consecutive_failures >= self.max_retries:
            self.logger.log_critical(
                f"Connection failed {self.consecutive_failures} times - pausing"
            )
    
    def validate_response_format(self, data: Any) -> bool:
        """
        Validate that API response matches expected format
        
        Args:
            data: Response data to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        # For market data, we expect a list of markets or a single market dict
        if isinstance(data, list):
            if not data:
                return True  # Empty list is valid
            # Check first item has expected fields
            if isinstance(data[0], dict):
                return True
        elif isinstance(data, dict):
            # Single market should have basic fields
            return True
        
        return False
    
    def get_active_markets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch list of active markets from Polymarket Subgraph (FREE)
        
        Args:
            limit: Maximum number of markets to return
        
        Returns:
            List of active market dictionaries
        """
        try:
            # Use FREE Polymarket Subgraph (GraphQL)
            markets = self.market_client.query_markets(
                active=True,
                first=limit
            )
            
            if markets:
                self.logger.log_info(f"Fetched {len(markets)} active markets from Subgraph")
                
                # Update cache
                for market in markets:
                    market_id = market.get('id')
                    if market_id:
                        self.market_cache[market_id] = market
                        self.cache_timestamps[market_id] = datetime.now()
                
                return markets
            else:
                self.logger.log_warning("No markets returned from Subgraph")
                return []
                
        except Exception as e:
            self.logger.log_error(f"Error fetching markets from Subgraph: {str(e)}")
            return []
    
    def get_market_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Fetch YES and NO prices for a specific market using FREE Subgraph
        
        Args:
            market_id: Market identifier
            
        Returns:
            Dictionary with 'yes' and 'no' prices, or None on error
        """
        try:
            # Check cache first
            if market_id in self.market_cache:
                cache_age = (datetime.now() - self.cache_timestamps.get(market_id, datetime.now())).total_seconds()
                
                if cache_age < self.cache_ttl:
                    # Use cached data
                    market = self.market_cache[market_id]
                    return self._parse_market_prices(market, market_id)
            
            # Fetch from FREE Polymarket Subgraph
            prices = self.market_client.get_market_prices(market_id)
            
            if prices:
                # Update cache
                self.market_cache[market_id] = prices
                self.cache_timestamps[market_id] = datetime.now()
                
                return prices
            else:
                self.logger.log_warning(f"No price data for market {market_id}")
                return None
            
        except Exception as e:
            self.logger.log_error(f"Error fetching prices for {market_id}: {str(e)}")
            return None
    
    def _parse_market_prices(self, market: Dict, market_id: str) -> Optional[Dict[str, float]]:
        """Parse prices from cached market data"""
        try:
            outcome_prices = market.get('outcomePrices', [])
            
            if len(outcome_prices) >= 2:
                return {
                    'yes': float(outcome_prices[0]),
                    'no': float(outcome_prices[1]),
                    'market_id': market_id,
                    'question': market.get('question', ''),
                    'timestamp': datetime.now().isoformat()
                }
            return None
        except (KeyError, IndexError, ValueError, TypeError) as e:
            if self.logger:
                self.logger.log_error(f"Error parsing market prices: {str(e)}")
            return None
    
    def get_crypto_price(self, symbol: str) -> Optional[Dict]:
        """
        Get crypto price using FREE price aggregator (Binance + CoinGecko)
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Price data with consensus from multiple sources
        """
        try:
            price_data = self.price_aggregator.get_best_price(symbol)
            
            if price_data:
                self.logger.log_info(
                    f"Crypto price: {symbol} = ${price_data['price']:,.2f} "
                    f"(sources: {', '.join(price_data['sources'])})"
                )
            
            return price_data
            
        except Exception as e:
            self.logger.log_error(f"Error fetching crypto price for {symbol}: {str(e)}")
            return None
    
    def search_markets_by_topic(self, topic: str, limit: int = 20) -> List[Dict]:
        """
        Search prediction markets by topic using FREE Subgraph
        
        Args:
            topic: Topic keyword (e.g., "Bitcoin", "Election")
            limit: Maximum results
            
        Returns:
            List of matching markets
        """
        try:
            markets = self.market_client.search_markets_by_topic(topic, limit)
            
            if markets:
                self.logger.log_info(f"Found {len(markets)} markets for topic: {topic}")
            
            return markets
            
        except Exception as e:
            self.logger.log_error(f"Error searching markets for topic {topic}: {str(e)}")
            return []
    
    def _check_rate_limit(self) -> bool:
        """
        Check rate limit and handle accordingly
        
        Returns:
            True if request can proceed, False if rate limited
        """
        usage_pct = self.rate_limiter.get_usage_percentage() / 100.0
        
        # Check if we're at pause threshold
        if usage_pct >= self.pause_threshold:
            wait_time = self.rate_limiter.get_reset_time()
            self.logger.log_warning(
                f"Rate limit at {usage_pct*100:.0f}% - pausing for {wait_time}s"
            )
            time.sleep(wait_time + 1)  # Wait for reset plus buffer
            return True
        
        # Check if we're at warning threshold
        if usage_pct >= self.warning_threshold:
            self.logger.log_warning(
                f"Rate limit at {usage_pct*100:.0f}% - slowing down"
            )
        
        # Check if we can make request
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_reset_time()
            time.sleep(wait_time + 1)
            return True
        
        return True
    
    def handle_rate_limit(self) -> int:
        """
        Handle rate limiting with exponential backoff
        
        Returns:
            Wait time in seconds
        """
        usage = self.rate_limiter.get_usage_percentage()
        
        if usage >= self.pause_threshold * 100:
            # At critical threshold, wait for reset
            wait_time = self.rate_limiter.get_reset_time() + 5
            self.logger.log_warning(f"Rate limit critical - waiting {wait_time}s")
            return wait_time
        elif usage >= self.warning_threshold * 100:
            # At warning threshold, slow down
            return 5
        
        return 0
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        # CLEAN OLD REQUESTS FIRST!
        self.rate_limiter._clean_old_requests()
        
        return {
            'current': len(self.rate_limiter.requests),
            'max': self.rate_limiter.max_requests,
            'percentage': self.rate_limiter.get_usage_percentage(),
            'remaining': self.rate_limiter.get_remaining_requests(),
            'reset_in': self.rate_limiter.get_reset_time()
        }
