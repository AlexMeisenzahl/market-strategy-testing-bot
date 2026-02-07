"""
Monitor Module - Price monitoring and API handling for Polymarket

Handles:
- API connection to Polymarket (Live API + Free Subgraph)
- Free crypto price APIs (Binance + CoinGecko)
- Rate limit tracking and management
- Connection health monitoring
- Data validation
- Intelligent fallback between data sources
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from logger import get_logger

# Import free API clients (from PR #8)
from apis.price_aggregator import PriceAggregator
from apis.polymarket_subgraph import PolymarketSubgraph

# Import Live API client (from PR #6) - optional
try:
    from polymarket_api import PolymarketAPI
except ImportError:
    PolymarketAPI = None  # Will be disabled if not available


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
        Initialize Polymarket monitor with intelligent data source fallback
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Initialize free API clients (from PR #8)
        self.price_aggregator = PriceAggregator(logger=self.logger)
        self.subgraph_client = PolymarketSubgraph()
        
        # Initialize Live API client (from PR #6) - OPTIONAL
        polymarket_config = config.get('polymarket', {}).get('api', {})
        self.live_api_enabled = polymarket_config.get('enabled', False)
        
        if self.live_api_enabled and PolymarketAPI:
            self.api = PolymarketAPI(
                timeout=polymarket_config.get('timeout', 10),
                retry_attempts=polymarket_config.get('retry_attempts', 3)
            )
        else:
            self.api = None
        
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
        # Use live data if enabled
        if self.live_api_enabled and self.api:
            try:
                return self.api.get_markets(active=True, limit=100)
            except Exception as e:
                self.logger.log_error(f"Error fetching live markets: {str(e)}")
                return []
        
        # Fallback to empty list for simulated mode
        # (simulated markets are handled in bot.py with _get_demo_markets)
        return []
    
    def get_market_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Fetch YES and NO prices for a specific market with intelligent fallback:
        1. Try Live API (if enabled)
        2. Fallback to Subgraph (always available)
        3. Final fallback to simulated prices (for testing)
        
        Args:
            market_id: Market identifier
            
        Returns:
            Dictionary with 'yes' and 'no' prices, or None on error
        """
        # Try Live API first if enabled
        if self.live_api_enabled and self.api:
            try:
                prices = self.api.get_market_prices(market_id)
                if prices:
                    return {
                        'yes': prices.get('yes', 0.5),
                        'no': prices.get('no', 0.5),
                        'market_id': market_id,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                self.logger.log_warning(f"Live API failed, falling back to Subgraph: {e}")
        
        # Fallback to free Subgraph
        try:
            prices = self.subgraph_client.get_market_prices(market_id)
            if prices:
                return prices
        except Exception as e:
            self.logger.log_warning(f"Subgraph failed, using simulated prices: {e}")
        
        # Final fallback: Generate simulated prices for testing
        import random
        yes_price = round(random.uniform(0.40, 0.60), 3)
        no_price = round(random.uniform(0.40, 0.60), 3)
        
        return {
            'yes': yes_price,
            'no': no_price,
            'market_id': market_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_crypto_price(self, symbol: str) -> Optional[Dict]:
        """
        Get crypto price using free aggregator (Binance + CoinGecko)
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dictionary with price information and sources, or None on error
        """
        return self.price_aggregator.get_best_price(symbol)
    
    def _get_live_market_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Fetch real market prices from Polymarket API
        
        Args:
            market_id: Market identifier (can be token ID)
            
        Returns:
            Dictionary with 'yes' and 'no' prices, or None on error
        """
        try:
            # Fetch prices from API using our API client
            prices = self.api.get_market_prices(market_id)
            
            if prices is None:
                self.logger.log_warning(f"Failed to fetch live prices for {market_id}")
                return None
            
            # Our API already returns in the correct format with 'yes' and 'no'
            return {
                'yes': prices.get('yes', 0.5),
                'no': prices.get('no', 0.5),
                'market_id': market_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log_error(f"Error fetching live prices for {market_id}: {str(e)}")
            return None
    
    def _get_simulated_market_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Generate simulated market prices for testing
        
        Args:
            market_id: Market identifier
            
        Returns:
            Dictionary with 'yes' and 'no' prices
        """
        # Check rate limit
        if not self._check_rate_limit():
            return None
        
        try:
            # Add delay between requests
            time.sleep(self.request_delay)
            
            if self.live_api_enabled:
                # Use LIVE Polymarket API
                prices = self.api.get_market_prices(market_id)
                
                self.rate_limiter.record_request()
                
                if prices:
                    return {
                        'yes': prices.get('yes', 0.5),
                        'no': prices.get('no', 0.5),
                        'market_id': market_id,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    # Fallback to simulated if API fails
                    self.logger.log_warning(
                        f"Live API failed for {market_id}, using fallback data"
                    )
            
            # Fallback: Simulate prices (for when API is disabled or fails)
            # This ensures paper trading can continue even if API is unavailable
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
