"""
Polymarket API Integration Module

Handles live data fetching from Polymarket's public APIs:
- Gamma API: Market listings and metadata
- CLOB API: Order book and price data

Features:
- Rate limiting
- Response caching
- Error handling with exponential backoff
- No authentication required for public data
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from logger import get_logger


class PolymarketAPI:
    """Client for Polymarket public APIs"""
    
    # API endpoints (public, no authentication needed)
    GAMMA_API_URL = "https://gamma-api.polymarket.com"
    CLOB_API_URL = "https://clob.polymarket.com"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Polymarket API client
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = get_logger()
        
        # Extract polymarket config if available
        polymarket_config = config.get('polymarket', {})
        
        # API endpoints
        self.gamma_url = polymarket_config.get('api_base_url', self.GAMMA_API_URL)
        self.clob_url = polymarket_config.get('clob_api_url', self.CLOB_API_URL)
        
        # Rate limiting
        self.rate_limit = polymarket_config.get('rate_limit_per_minute', 60)
        self.request_timestamps = []
        
        # Caching
        self.cache_duration = polymarket_config.get('cache_duration_seconds', 15)
        self.cache = {}
        
        # Request settings
        self.timeout = config.get('api_timeout_seconds', 10)
        self.max_retries = config.get('max_retries', 3)
        self.backoff_factor = 2
        
    def _check_rate_limit(self) -> bool:
        """
        Check if we can make a request without exceeding rate limit
        
        Returns:
            True if request can proceed, False if rate limited
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=60)
        
        # Clean old timestamps
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff]
        
        # Check if under limit
        if len(self.request_timestamps) >= self.rate_limit:
            self.logger.log_warning(f"Rate limit reached ({self.rate_limit}/min)")
            return False
        
        return True
    
    def _record_request(self) -> None:
        """Record that a request was made"""
        self.request_timestamps.append(datetime.now())
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache if available and not expired
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not available/expired
        """
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            age = (datetime.now() - timestamp).total_seconds()
            
            if age < self.cache_duration:
                # Cache hit
                return cached_data
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """
        Save data to cache
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        self.cache[cache_key] = (data, datetime.now())
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request with retry logic
        
        Args:
            url: Request URL
            params: Query parameters
            
        Returns:
            Response JSON or None on error
        """
        # Check rate limit
        if not self._check_rate_limit():
            # Wait for rate limit to reset
            time.sleep(1)
            return None
        
        # Try with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    headers={'User-Agent': 'PolymarketBot/1.0'}
                )
                
                self._record_request()
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited
                    wait_time = (2 ** attempt) * self.backoff_factor
                    self.logger.log_warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.log_error(f"API error: HTTP {response.status_code}")
                    return None
                    
            except requests.exceptions.Timeout:
                self.logger.log_warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
            except requests.exceptions.ConnectionError as e:
                self.logger.log_warning(f"Connection error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
            except Exception as e:
                self.logger.log_error(f"Unexpected error: {str(e)}")
                return None
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                wait_time = (2 ** attempt) * self.backoff_factor
                time.sleep(wait_time)
        
        return None
    
    def fetch_markets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch active markets from Polymarket
        
        Args:
            limit: Maximum number of markets to fetch
            
        Returns:
            List of market dictionaries
        """
        cache_key = f"markets_{limit}"
        
        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Fetch from API
        url = f"{self.gamma_url}/markets"
        params = {
            'closed': 'false',
            'limit': limit
        }
        
        # Fetching markets from API
        data = self._make_request(url, params)
        
        if data is None:
            self.logger.log_error("Failed to fetch markets")
            return []
        
        # Handle different response formats
        markets = data if isinstance(data, list) else data.get('data', [])
        
        # Cache the results
        self._save_to_cache(cache_key, markets)
        
        # Successfully fetched markets
        return markets
    
    def fetch_market_prices(self, token_id: str) -> Optional[Dict[str, float]]:
        """
        Fetch current prices for a market token
        
        Args:
            token_id: Market token ID
            
        Returns:
            Dictionary with 'bid' and 'ask' prices, or None on error
        """
        cache_key = f"prices_{token_id}"
        
        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Fetch from CLOB API
        url = f"{self.clob_url}/price"
        params = {'token_id': token_id}
        
        data = self._make_request(url, params)
        
        if data is None:
            return None
        
        try:
            # Extract bid/ask prices
            prices = {
                'bid': float(data.get('bid', 0)),
                'ask': float(data.get('ask', 0)),
                'mid': float(data.get('mid', 0)),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the results
            self._save_to_cache(cache_key, prices)
            
            return prices
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.log_error(f"Error parsing price data for {token_id}: {str(e)}")
            return None
    
    def fetch_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch events (prediction markets) from Polymarket
        
        Args:
            limit: Maximum number of events to fetch
            
        Returns:
            List of event dictionaries
        """
        cache_key = f"events_{limit}"
        
        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Fetch from API
        url = f"{self.gamma_url}/events"
        params = {
            'closed': 'false',
            'limit': limit
        }
        
        # Fetching events from API
        data = self._make_request(url, params)
        
        if data is None:
            self.logger.log_error("Failed to fetch events")
            return []
        
        # Handle different response formats
        events = data if isinstance(data, list) else data.get('data', [])
        
        # Cache the results
        self._save_to_cache(cache_key, events)
        
        # Successfully fetched events
        return events
    
    def get_market_by_id(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific market by ID
        
        Args:
            market_id: Market ID
            
        Returns:
            Market dictionary or None if not found
        """
        cache_key = f"market_{market_id}"
        
        # Check cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Fetch from API
        url = f"{self.gamma_url}/markets/{market_id}"
        
        data = self._make_request(url)
        
        if data is not None:
            self._save_to_cache(cache_key, data)
        
        return data
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache.clear()
        # Cache cleared
