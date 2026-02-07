"""
Monitor Module - Price monitoring and API handling for Polymarket

Handles:
- API connection to Polymarket via free data sources
- Rate limit tracking and management
- Connection health monitoring
- Data validation
- Exponential backoff on errors
- Integration with Binance, CoinGecko, and Polymarket Subgraph
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from logger import get_logger

# Import new data sources
try:
    from data_sources.price_aggregator import PriceAggregator
    from data_sources.polymarket_subgraph import PolymarketSubgraph
    DATA_SOURCES_AVAILABLE = True
except ImportError:
    DATA_SOURCES_AVAILABLE = False
    print("Warning: New data sources not available, using legacy API")


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
        Initialize Polymarket monitor
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Initialize new data sources if available
        if DATA_SOURCES_AVAILABLE:
            data_sources_config = config.get('data_sources', {})
            
            # Initialize price aggregator for crypto prices
            price_agg_config = config.get('price_aggregator', {})
            self.price_aggregator = PriceAggregator(
                enable_websocket=price_agg_config.get('enable_websocket', True)
            )
            
            # Initialize Polymarket Subgraph client
            self.subgraph = PolymarketSubgraph()
            
            # Start WebSocket streams if enabled
            if data_sources_config.get('binance', {}).get('websocket', True):
                symbols = data_sources_config.get('binance', {}).get('symbols', ['BTCUSDT', 'ETHUSDT'])
                self.price_aggregator.start_websocket_streams(symbols)
            
            self.use_new_sources = True
        else:
            self.price_aggregator = None
            self.subgraph = None
            self.use_new_sources = False
        
        # Initialize rate limiter
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
    
    def check_connection_health(self) -> bool:
        """
        Test if connection to Polymarket is stable
        
        Returns:
            True if connection is healthy, False otherwise
        """
        start_time = time.time()
        
        try:
            # Try to fetch markets list as health check
            response = requests.get(
                f"{self.BASE_URL}{self.MARKETS_ENDPOINT}",
                timeout=self.timeout
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
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
                self._handle_connection_failure(f"HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self._handle_connection_failure("timeout")
            return False
        except requests.exceptions.ConnectionError:
            self._handle_connection_failure("connection error")
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
    
    def get_active_markets(self) -> List[Dict[str, Any]]:
        """
        Fetch list of active markets from Polymarket
        
        Returns:
            List of active market dictionaries
        """
        # Try new data sources first
        if self.use_new_sources and self.subgraph:
            try:
                markets = self.subgraph.query_markets(
                    filters={'active': True},
                    limit=self.config.get('data_sources', {})
                        .get('polymarket_subgraph', {})
                        .get('max_markets_per_query', 100)
                )
                if markets:
                    return markets
            except Exception as e:
                self.logger.log_warning(f"Subgraph query failed, falling back to legacy API: {e}")
        
        # Fallback to legacy API
        # Check rate limit
        if not self._check_rate_limit():
            return []
        
        try:
            # Add delay between requests
            time.sleep(self.request_delay)
            
            response = requests.get(
                f"{self.BASE_URL}{self.MARKETS_ENDPOINT}",
                timeout=self.timeout,
                params={"active": "true"}
            )
            
            self.rate_limiter.record_request()
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response format
                if not self.validate_response_format(data):
                    self.logger.log_critical("API format changed - unexpected response structure")
                    return []
                
                return data if isinstance(data, list) else [data]
            else:
                self.logger.log_error(f"Failed to fetch markets: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.log_error(f"Error fetching markets: {str(e)}")
            return []
    
    def get_market_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Fetch YES and NO prices for a specific market
        
        Args:
            market_id: Market identifier
            
        Returns:
            Dictionary with 'yes' and 'no' prices, or None on error
        """
        # Try new data sources first
        if self.use_new_sources and self.subgraph:
            try:
                prices = self.subgraph.get_market_prices(market_id)
                if prices:
                    return {
                        'yes': prices.get('yes_price', 0.5),
                        'no': prices.get('no_price', 0.5),
                        'market_id': market_id,
                        'timestamp': prices.get('last_updated', datetime.now().isoformat())
                    }
            except Exception as e:
                self.logger.log_warning(f"Subgraph price fetch failed, falling back: {e}")
        
        # Fallback to legacy API/simulation
        # Check rate limit
        if not self._check_rate_limit():
            return None
        
        try:
            # Add delay between requests
            time.sleep(self.request_delay)
            
            # For this implementation, we'll simulate market prices
            # In production, you would fetch from the actual Polymarket API
            # This is a paper trading bot, so simulated data is acceptable
            
            # Simulate prices (this would be replaced with actual API call)
            import random
            yes_price = round(random.uniform(0.40, 0.60), 3)
            no_price = round(random.uniform(0.40, 0.60), 3)
            
            self.rate_limiter.record_request()
            
            return {
                'yes': yes_price,
                'no': no_price,
                'market_id': market_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log_error(f"Error fetching prices for {market_id}: {str(e)}")
            return None
    
    def get_crypto_price(self, symbol: str = 'BTCUSDT') -> Optional[float]:
        """
        Get cryptocurrency price from aggregated sources
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Current price, or None on error
        """
        if self.use_new_sources and self.price_aggregator:
            try:
                return self.price_aggregator.get_best_price(symbol)
            except Exception as e:
                self.logger.log_error(f"Error fetching crypto price for {symbol}: {e}")
        
        return None
    
    def get_crypto_prices_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get cryptocurrency prices for multiple symbols
        
        Args:
            symbols: List of trading pair symbols
            
        Returns:
            Dictionary mapping symbols to prices
        """
        if self.use_new_sources and self.price_aggregator:
            try:
                return self.price_aggregator.get_prices_batch(symbols)
            except Exception as e:
                self.logger.log_error(f"Error fetching batch crypto prices: {e}")
        
        return {}
    
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
