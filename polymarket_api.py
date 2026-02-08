"""
Live Polymarket API integration
Documentation: https://docs.polymarket.com/

Official Polymarket CLOB (Central Limit Order Book) API client
- Public endpoints (no authentication needed for market data)
- Rate limiting: respects API limits with exponential backoff
- Error handling: retries with exponential backoff
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from logger import get_logger


class PolymarketAPI:
    """
    Official Polymarket API client for accessing market data

    This client interfaces with the Polymarket CLOB API to fetch:
    - Active markets and market details
    - Real-time YES/NO prices
    - Order book data for liquidity analysis
    """

    BASE_URL = "https://clob.polymarket.com"

    def __init__(self, timeout: int = 10, retry_attempts: int = 3):
        """
        Initialize Polymarket API client

        Args:
            timeout: Request timeout in seconds (default: 10)
            retry_attempts: Number of retry attempts on failure (default: 3)
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.logger = get_logger()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Market-Strategy-Testing-Bot/1.0",
                "Accept": "application/json",
            }
        )

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Optional[Any]:
        """
        Make HTTP request with exponential backoff retry logic

        Args:
            endpoint: API endpoint path
            params: Query parameters
            retry_count: Current retry attempt number

        Returns:
            Response JSON data or None on failure
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)

            # Check for rate limiting
            if response.status_code == 429:
                if retry_count < self.retry_attempts:
                    # Exponential backoff: 2^retry_count seconds
                    wait_time = 2**retry_count
                    self.logger.log_warning(
                        f"Rate limited by API. Waiting {wait_time}s before retry..."
                    )
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    self.logger.log_error("Rate limit exceeded, max retries reached")
                    return None

            # Success
            if response.status_code == 200:
                return response.json()

            # Client error (4xx)
            if 400 <= response.status_code < 500:
                self.logger.log_error(
                    f"API client error {response.status_code}: {response.text}"
                )
                return None

            # Server error (5xx) - retry with backoff
            if 500 <= response.status_code < 600:
                if retry_count < self.retry_attempts:
                    wait_time = 2**retry_count
                    self.logger.log_warning(
                        f"API server error {response.status_code}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    self.logger.log_error(
                        f"API server error {response.status_code}, max retries reached"
                    )
                    return None

            return None

        except requests.exceptions.Timeout:
            if retry_count < self.retry_attempts:
                wait_time = 2**retry_count
                self.logger.log_warning(f"Request timeout. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self._make_request(endpoint, params, retry_count + 1)
            else:
                self.logger.log_error("Request timeout, max retries reached")
                return None

        except requests.exceptions.ConnectionError as e:
            if retry_count < self.retry_attempts:
                wait_time = 2**retry_count
                self.logger.log_warning(
                    f"Connection error: {str(e)}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                return self._make_request(endpoint, params, retry_count + 1)
            else:
                self.logger.log_error(
                    f"Connection error, max retries reached: {str(e)}"
                )
                return None

        except Exception as e:
            self.logger.log_error(f"Unexpected API error: {str(e)}")
            return None

    def get_markets(
        self, active: bool = True, limit: int = 100, offset: int = 0
    ) -> List[Dict]:
        """
        Fetch active markets from Polymarket

        Args:
            active: If True, only return active markets (default: True)
            limit: Maximum number of markets to return (default: 100)
            offset: Pagination offset (default: 0)

        Returns:
            List of market objects with:
            - condition_id (unique identifier)
            - question (market question)
            - outcomes (YES/NO)
            - end_date_iso (market closing date)
            - volume (trading volume)
            - liquidity (available liquidity)
            - tokens (token addresses for YES/NO)
        """
        params = {"limit": limit, "offset": offset}

        if active:
            params["closed"] = "false"

        data = self._make_request("/markets", params)

        if data is None:
            return []

        # Handle both list and single market response
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            self.logger.log_error(f"Unexpected markets response format: {type(data)}")
            return []

    def get_market(self, condition_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific market

        Args:
            condition_id: Unique market identifier

        Returns:
            Market object or None if not found
        """
        data = self._make_request(f"/markets/{condition_id}")
        return data

    def get_market_prices(self, condition_id: str) -> Dict[str, float]:
        """
        Get current YES/NO prices for a market

        Args:
            condition_id: Unique market identifier

        Returns:
            Dictionary with 'yes' and 'no' prices
            Example: {"yes": 0.52, "no": 0.48}
        """
        # First get market details to find token IDs
        market = self.get_market(condition_id)

        if not market or "tokens" not in market:
            self.logger.log_error(f"Could not get market details for {condition_id}")
            return {"yes": 0.5, "no": 0.5}  # Return default if unavailable

        tokens = market.get("tokens", [])
        if len(tokens) < 2:
            self.logger.log_error(f"Market {condition_id} has insufficient tokens")
            return {"yes": 0.5, "no": 0.5}

        # Get prices for YES and NO tokens
        yes_token = tokens[0].get("token_id", "")
        no_token = tokens[1].get("token_id", "")

        yes_price = self._get_token_price(yes_token)
        no_price = self._get_token_price(no_token)

        return {
            "yes": yes_price if yes_price is not None else 0.5,
            "no": no_price if no_price is not None else 0.5,
        }

    def _get_token_price(self, token_id: str) -> Optional[float]:
        """
        Get current price for a specific token

        Args:
            token_id: Token identifier

        Returns:
            Price as float or None if unavailable
        """
        data = self._make_request("/price", params={"token_id": token_id})

        if data and "price" in data:
            return float(data["price"])

        return None

    def get_orderbook(self, token_id: str) -> Dict:
        """
        Get full orderbook for deep liquidity analysis

        Args:
            token_id: Token identifier for YES or NO outcome

        Returns:
            Orderbook with bids and asks:
            {
                'bids': [{'price': 0.51, 'size': 100}, ...],
                'asks': [{'price': 0.52, 'size': 150}, ...]
            }
        """
        data = self._make_request("/book", params={"token_id": token_id})

        if data is None:
            return {"bids": [], "asks": []}

        return {"bids": data.get("bids", []), "asks": data.get("asks", [])}

    def get_market_trades(self, condition_id: str, limit: int = 100) -> List[Dict]:
        """
        Get recent trades for a market

        Args:
            condition_id: Unique market identifier
            limit: Maximum number of trades to return (default: 100)

        Returns:
            List of recent trades with price, size, and timestamp
        """
        params = {"market": condition_id, "limit": limit}

        data = self._make_request("/trades", params)

        if data is None:
            return []

        if isinstance(data, list):
            return data

        return []

    def check_health(self) -> bool:
        """
        Check if Polymarket API is accessible

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/markets", params={"limit": 1}, timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
