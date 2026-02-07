"""
Polymarket Subgraph GraphQL Client
Free, no authentication required
Unlimited rate limits (decentralized)
"""

import requests
import time
from typing import Dict, Optional, List


class PolymarketSubgraph:
    """GraphQL client for Polymarket Subgraph on The Graph"""
    
    # Primary subgraph endpoint (free, no authentication required)
    SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"
    
    # Note: The Graph's decentralized network provides free public access
    # No alternative endpoints are needed for the free tier
    
    def __init__(self, query_timeout_seconds: int = 10):
        """
        Initialize Polymarket Subgraph client
        
        Args:
            query_timeout_seconds: Timeout for GraphQL queries (default: 10)
        """
        self.timeout = query_timeout_seconds
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Minimum time between requests
        
    def _make_graphql_request(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """
        Execute GraphQL query
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Query response data or None on error
        """
        # Basic rate limiting (be respectful)
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
            
            response = requests.post(
                self.SUBGRAPH_URL,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
                elif 'errors' in data:
                    # GraphQL errors
                    return None
            
            return None
            
        except Exception:
            return None
    
    def get_active_markets(self, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get active markets ordered by liquidity
        
        Args:
            limit: Maximum number of markets to return (default: 10)
            
        Returns:
            List of market dictionaries or None on error
        """
        query = """
        query GetActiveMarkets($limit: Int!) {
            markets(
                first: $limit,
                orderBy: liquidityParameter,
                orderDirection: desc,
                where: {closed: false}
            ) {
                id
                question
                outcomes
                outcomePrices
                liquidityParameter
                volume
                endDate
                createdAt
                creator
            }
        }
        """
        
        data = self._make_graphql_request(query, {"limit": limit})
        
        if data and 'markets' in data:
            return data['markets']
        
        return None
    
    def get_market_by_id(self, market_id: str) -> Optional[Dict]:
        """
        Get specific market by ID
        
        Args:
            market_id: Market contract address
            
        Returns:
            Market data dictionary or None on error
        """
        query = """
        query GetMarket($id: ID!) {
            market(id: $id) {
                id
                question
                outcomes
                outcomePrices
                liquidityParameter
                volume
                endDate
                createdAt
                closed
                resolved
                creator
            }
        }
        """
        
        data = self._make_graphql_request(query, {"id": market_id.lower()})
        
        if data and 'market' in data:
            return data['market']
        
        return None
    
    def get_market_odds(self, market_id: str) -> Optional[Dict]:
        """
        Get current odds (prices) for a market
        
        Args:
            market_id: Market contract address
            
        Returns:
            Dictionary with 'yes' and 'no' prices, or None on error
        """
        market = self.get_market_by_id(market_id)
        
        if market and 'outcomePrices' in market:
            prices = market['outcomePrices']
            
            # Convert from subgraph format (typically array of prices)
            if isinstance(prices, list) and len(prices) >= 2:
                return {
                    'yes': float(prices[0]) if prices[0] else 0.5,
                    'no': float(prices[1]) if prices[1] else 0.5,
                    'market_id': market_id,
                    'question': market.get('question', ''),
                    'volume': float(market.get('volume', 0)),
                    'liquidity': float(market.get('liquidityParameter', 0))
                }
        
        return None
    
    def search_markets(self, search_term: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Search markets by question text
        
        Args:
            search_term: Text to search for in market questions
            limit: Maximum number of results (default: 10)
            
        Returns:
            List of matching markets or None on error
        """
        query = """
        query SearchMarkets($limit: Int!) {
            markets(
                first: $limit,
                orderBy: liquidityParameter,
                orderDirection: desc,
                where: {closed: false}
            ) {
                id
                question
                outcomes
                outcomePrices
                volume
                liquidityParameter
                endDate
            }
        }
        """
        
        data = self._make_graphql_request(query, {"limit": limit * 2})
        
        if data and 'markets' in data:
            # Filter by search term (subgraph doesn't support text search directly)
            markets = data['markets']
            search_lower = search_term.lower()
            filtered = [
                m for m in markets 
                if search_lower in m.get('question', '').lower()
            ]
            return filtered[:limit]
        
        return None
    
    def get_markets_by_volume(self, limit: int = 10, min_volume: float = 0) -> Optional[List[Dict]]:
        """
        Get markets with highest trading volume
        
        Args:
            limit: Maximum number of markets to return (default: 10)
            min_volume: Minimum volume threshold (default: 0)
            
        Returns:
            List of market dictionaries or None on error
        """
        query = """
        query GetMarketsByVolume($limit: Int!, $minVolume: String!) {
            markets(
                first: $limit,
                orderBy: volume,
                orderDirection: desc,
                where: {closed: false, volume_gt: $minVolume}
            ) {
                id
                question
                outcomes
                outcomePrices
                volume
                liquidityParameter
                endDate
            }
        }
        """
        
        data = self._make_graphql_request(
            query, 
            {"limit": limit, "minVolume": str(min_volume)}
        )
        
        if data and 'markets' in data:
            return data['markets']
        
        return None
    
    def ping(self) -> bool:
        """
        Test connectivity to Polymarket Subgraph
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            query = """
            query {
                markets(first: 1) {
                    id
                }
            }
            """
            
            data = self._make_graphql_request(query)
            return data is not None and 'markets' in data
            
        except Exception:
            return False
    
    def get_market_statistics(self) -> Optional[Dict]:
        """
        Get overall Polymarket statistics
        
        Returns:
            Statistics dictionary or None on error
        """
        query = """
        query {
            markets(first: 1000, where: {closed: false}) {
                volume
                liquidityParameter
            }
        }
        """
        
        data = self._make_graphql_request(query)
        
        if data and 'markets' in data:
            markets = data['markets']
            total_volume = sum(float(m.get('volume', 0)) for m in markets)
            total_liquidity = sum(float(m.get('liquidityParameter', 0)) for m in markets)
            
            return {
                'total_markets': len(markets),
                'total_volume': total_volume,
                'total_liquidity': total_liquidity,
                'average_volume': total_volume / len(markets) if markets else 0,
                'average_liquidity': total_liquidity / len(markets) if markets else 0
            }
        
        return None
