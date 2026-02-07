"""
CoinGecko Client - Free API for Crypto Prices and Market Data

Provides:
- 10,000+ cryptocurrency prices
- Market data (market cap, volume, etc.)
- Historical charts
- 10-50 requests/minute (FREE, no API key)
- Used by DeFi apps, portfolio trackers

No API keys required.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class CoinGeckoClient:
    """CoinGecko Free API Client for Crypto Prices"""
    
    # Public CoinGecko API (no authentication required)
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Rate limits (free tier)
    MAX_REQUESTS_PER_MINUTE = 50
    REQUEST_DELAY = 1.5  # Seconds between requests
    
    # Common coin ID mappings
    COIN_ID_MAP = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'USDT': 'tether',
        'BNB': 'binancecoin',
        'SOL': 'solana',
        'XRP': 'ripple',
        'USDC': 'usd-coin',
        'ADA': 'cardano',
        'AVAX': 'avalanche-2',
        'DOGE': 'dogecoin',
        'MATIC': 'matic-network',
        'DOT': 'polkadot',
        'UNI': 'uniswap',
        'LINK': 'chainlink',
        'ATOM': 'cosmos'
    }
    
    def __init__(self):
        """Initialize CoinGecko client"""
        self.last_request_time: Optional[datetime] = None
        self.request_times: List[datetime] = []
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = 60  # Cache prices for 60 seconds
    
    def get_price(
        self,
        coin_id: str,
        vs_currency: str = 'usd',
        use_cache: bool = True
    ) -> Optional[float]:
        """
        Get current price for a cryptocurrency
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
                    Can also use symbol (e.g., 'BTC', 'ETH')
            vs_currency: Currency to quote price in (default: 'usd')
            use_cache: Whether to use cached prices
        
        Returns:
            Current price or None if unavailable
        """
        # Convert symbol to coin ID if needed
        coin_id = self._resolve_coin_id(coin_id)
        
        # Check cache first
        if use_cache:
            cached_price = self._get_from_cache(coin_id, vs_currency)
            if cached_price is not None:
                return cached_price
        
        # Respect rate limits
        self._wait_for_rate_limit()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/simple/price",
                params={
                    'ids': coin_id,
                    'vs_currencies': vs_currency,
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true',
                    'include_market_cap': 'true'
                },
                timeout=10
            )
            
            self._record_request()
            
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    price = data[coin_id].get(vs_currency)
                    
                    # Update cache
                    cache_key = f"{coin_id}:{vs_currency}"
                    self.cache[cache_key] = {
                        'price': price,
                        'timestamp': datetime.now(),
                        'data': data[coin_id]
                    }
                    
                    return price
            
            elif response.status_code == 429:
                print("CoinGecko rate limit exceeded - waiting...")
                time.sleep(60)  # Wait a minute before retrying
        
        except Exception as e:
            print(f"CoinGecko API error for {coin_id}: {e}")
        
        return None
    
    def get_prices(
        self,
        coin_ids: List[str],
        vs_currency: str = 'usd'
    ) -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies in a single request
        
        Args:
            coin_ids: List of CoinGecko coin IDs or symbols
            vs_currency: Currency to quote prices in (default: 'usd')
        
        Returns:
            Dictionary mapping coin ID to price
        """
        # Convert symbols to coin IDs
        coin_ids = [self._resolve_coin_id(cid) for cid in coin_ids]
        
        # Check cache for all coins
        prices = {}
        uncached_ids = []
        
        for coin_id in coin_ids:
            cached_price = self._get_from_cache(coin_id, vs_currency)
            if cached_price is not None:
                prices[coin_id] = cached_price
            else:
                uncached_ids.append(coin_id)
        
        # Fetch uncached prices
        if uncached_ids:
            self._wait_for_rate_limit()
            
            try:
                # CoinGecko allows up to 100 IDs per request
                response = requests.get(
                    f"{self.BASE_URL}/simple/price",
                    params={
                        'ids': ','.join(uncached_ids),
                        'vs_currencies': vs_currency,
                        'include_24hr_change': 'true'
                    },
                    timeout=10
                )
                
                self._record_request()
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for coin_id in uncached_ids:
                        if coin_id in data:
                            price = data[coin_id].get(vs_currency)
                            prices[coin_id] = price
                            
                            # Update cache
                            cache_key = f"{coin_id}:{vs_currency}"
                            self.cache[cache_key] = {
                                'price': price,
                                'timestamp': datetime.now(),
                                'data': data[coin_id]
                            }
            
            except Exception as e:
                print(f"CoinGecko API error: {e}")
        
        return prices
    
    def get_market_data(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed market data for a cryptocurrency
        
        Args:
            coin_id: CoinGecko coin ID or symbol
        
        Returns:
            Dictionary with market data or None
        """
        coin_id = self._resolve_coin_id(coin_id)
        
        self._wait_for_rate_limit()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/coins/{coin_id}",
                params={
                    'localization': 'false',
                    'tickers': 'false',
                    'community_data': 'false',
                    'developer_data': 'false'
                },
                timeout=10
            )
            
            self._record_request()
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('market_data', {})
                
                return {
                    'price_usd': market_data.get('current_price', {}).get('usd'),
                    'market_cap_usd': market_data.get('market_cap', {}).get('usd'),
                    'volume_24h_usd': market_data.get('total_volume', {}).get('usd'),
                    'price_change_24h': market_data.get('price_change_24h'),
                    'price_change_pct_24h': market_data.get('price_change_percentage_24h'),
                    'market_cap_rank': data.get('market_cap_rank'),
                    'high_24h': market_data.get('high_24h', {}).get('usd'),
                    'low_24h': market_data.get('low_24h', {}).get('usd'),
                    'ath': market_data.get('ath', {}).get('usd'),
                    'ath_date': market_data.get('ath_date', {}).get('usd'),
                    'atl': market_data.get('atl', {}).get('usd'),
                    'atl_date': market_data.get('atl_date', {}).get('usd')
                }
        
        except Exception as e:
            print(f"CoinGecko market data error for {coin_id}: {e}")
        
        return None
    
    def get_historical_prices(
        self,
        coin_id: str,
        vs_currency: str = 'usd',
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data
        
        Args:
            coin_id: CoinGecko coin ID or symbol
            vs_currency: Currency to quote prices in
            days: Number of days of history (1-365)
        
        Returns:
            List of price data points
        """
        coin_id = self._resolve_coin_id(coin_id)
        
        self._wait_for_rate_limit()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/coins/{coin_id}/market_chart",
                params={
                    'vs_currency': vs_currency,
                    'days': days,
                    'interval': 'daily' if days > 1 else 'hourly'
                },
                timeout=15
            )
            
            self._record_request()
            
            if response.status_code == 200:
                data = response.json()
                prices = data.get('prices', [])
                
                return [
                    {
                        'timestamp': datetime.fromtimestamp(p[0] / 1000),
                        'price': p[1]
                    }
                    for p in prices
                ]
        
        except Exception as e:
            print(f"CoinGecko historical data error for {coin_id}: {e}")
        
        return []
    
    def search_coins(self, query: str) -> List[Dict[str, str]]:
        """
        Search for coins by name or symbol
        
        Args:
            query: Search query
        
        Returns:
            List of matching coins with id, name, and symbol
        """
        self._wait_for_rate_limit()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                params={'query': query},
                timeout=10
            )
            
            self._record_request()
            
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                
                return [
                    {
                        'id': coin['id'],
                        'name': coin['name'],
                        'symbol': coin['symbol'].upper()
                    }
                    for coin in coins[:10]  # Return top 10 matches
                ]
        
        except Exception as e:
            print(f"CoinGecko search error: {e}")
        
        return []
    
    def _resolve_coin_id(self, coin_id: str) -> str:
        """Convert symbol to CoinGecko coin ID if needed"""
        # Check if it's already a coin ID (lowercase, may contain hyphens)
        if coin_id.islower() or '-' in coin_id:
            return coin_id
        
        # Try to map symbol to coin ID
        symbol = coin_id.upper()
        return self.COIN_ID_MAP.get(symbol, coin_id.lower())
    
    def _get_from_cache(self, coin_id: str, vs_currency: str) -> Optional[float]:
        """Get price from cache if available and fresh"""
        cache_key = f"{coin_id}:{vs_currency}"
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            age = (datetime.now() - cached['timestamp']).total_seconds()
            
            if age < self.cache_duration:
                return cached['price']
        
        return None
    
    def _wait_for_rate_limit(self) -> None:
        """Wait to respect rate limits"""
        if self.last_request_time is not None:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.REQUEST_DELAY:
                time.sleep(self.REQUEST_DELAY - elapsed)
    
    def _record_request(self) -> None:
        """Record that a request was made"""
        self.last_request_time = datetime.now()
        self.request_times.append(self.last_request_time)
        self._clean_old_requests()
    
    def _clean_old_requests(self) -> None:
        """Remove requests older than 1 minute"""
        cutoff = datetime.now() - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        self._clean_old_requests()
        
        return {
            'requests_used': len(self.request_times),
            'max_per_minute': self.MAX_REQUESTS_PER_MINUTE,
            'percentage': (len(self.request_times) / self.MAX_REQUESTS_PER_MINUTE) * 100,
            'cached_prices': len(self.cache)
        }
