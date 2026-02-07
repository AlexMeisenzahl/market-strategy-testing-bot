"""
Polymarket Subgraph Client - Free GraphQL prediction market data

Provides:
- On-chain prediction market data via The Graph
- GraphQL queries for markets, trades, outcomes
- Effectively unlimited rate limit (decentralized)
- No API key required
"""

import requests
import time
from typing import Dict, Optional, List, Any
from datetime import datetime


class PolymarketSubgraph:
    """
    Polymarket Subgraph client using The Graph protocol
    
    Features:
    - GraphQL API for on-chain data
    - Market conditions and outcomes
    - Trading volume and liquidity
    - Decentralized (no single point of failure)
    """
    
    # The Graph Polymarket subgraph endpoint
    GRAPHQL_URL = "https://api.thegraph.com/subgraphs/name/tokenunion/polymarket"
    
    # Alternative: Polymarket's own subgraph
    ALT_GRAPHQL_URL = "https://subgraph.polymarket.com/subgraphs/name/polymarket"
    
    def __init__(self, logger=None, use_alternative: bool = False):
        """
        Initialize Polymarket Subgraph client
        
        Args:
            logger: Optional logger instance
            use_alternative: Use alternative subgraph endpoint
        """
        self.logger = logger
        self.session = requests.Session()
        self.graphql_url = self.ALT_GRAPHQL_URL if use_alternative else self.GRAPHQL_URL
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Be respectful, even though it's "unlimited"
    
    def _rate_limit(self) -> None:
        """Enforce minimal rate limiting for politeness"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """
        Execute a GraphQL query
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Query result data or None on error
        """
        self._rate_limit()
        
        try:
            payload = {'query': query}
            if variables:
                payload['variables'] = variables
            
            response = self.session.post(
                self.graphql_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'errors' in result:
                    if self.logger:
                        self.logger.log_error(f"GraphQL errors: {result['errors']}")
                    return None
                
                return result.get('data')
            else:
                if self.logger:
                    self.logger.log_error(f"Subgraph API error: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.log_error(f"Subgraph connection error: {str(e)}")
            return None
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Subgraph query error: {str(e)}")
            return None
    
    def query_markets(self, 
                      active: bool = True, 
                      first: int = 10,
                      skip: int = 0,
                      question_contains: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query prediction markets
        
        Args:
            active: Filter for active markets only
            first: Number of results to return
            skip: Number of results to skip (pagination)
            question_contains: Filter by question text
            
        Returns:
            List of market dictionaries
            
        Example:
            >>> client = PolymarketSubgraph()
            >>> markets = client.query_markets(question_contains="Bitcoin")
            >>> for market in markets:
            ...     print(f"{market['question']}: {market['volumeUSD']}")
        """
        # Build where clause
        where_conditions = []
        if active:
            where_conditions.append('active: true')
        if question_contains:
            where_conditions.append(f'question_contains: "{question_contains}"')
        
        where_clause = ', '.join(where_conditions) if where_conditions else ''
        
        query = f"""
        {{
          markets(
            first: {first}, 
            skip: {skip}
            {', where: {' + where_clause + '}' if where_clause else ''}
            orderBy: volumeUSD
            orderDirection: desc
          ) {{
            id
            question
            outcomes
            outcomePrices
            liquidityParameter
            volumeUSD
            active
            closed
            marketMakerAddress
            createdAt
            updatedAt
          }}
        }}
        """
        
        data = self._execute_query(query)
        
        if data and 'markets' in data:
            markets = data['markets']
            
            if self.logger:
                self.logger.log_info(f"Subgraph: Fetched {len(markets)} markets")
            
            return markets
        
        return []
    
    def query_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Query a specific market by ID
        
        Args:
            market_id: Market identifier
            
        Returns:
            Market data dictionary or None
        """
        query = f"""
        {{
          market(id: "{market_id}") {{
            id
            question
            outcomes
            outcomePrices
            liquidityParameter
            volumeUSD
            active
            closed
            marketMakerAddress
            createdAt
            updatedAt
          }}
        }}
        """
        
        data = self._execute_query(query)
        
        if data and 'market' in data:
            return data['market']
        
        return None
    
    def get_market_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Get current YES/NO prices for a market
        
        Args:
            market_id: Market identifier
            
        Returns:
            Dictionary with 'yes' and 'no' prices
        """
        market = self.query_market(market_id)
        
        if not market:
            return None
        
        try:
            # Parse outcome prices
            outcome_prices = market.get('outcomePrices', [])
            outcomes = market.get('outcomes', [])
            
            if len(outcome_prices) >= 2:
                # Typically: [YES price, NO price]
                yes_price = float(outcome_prices[0]) if outcome_prices[0] else 0.5
                no_price = float(outcome_prices[1]) if outcome_prices[1] else 0.5
                
                return {
                    'yes': yes_price,
                    'no': no_price,
                    'market_id': market_id,
                    'question': market.get('question', ''),
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error parsing market prices: {str(e)}")
            return None
    
    def query_trades(self, market_id: Optional[str] = None, first: int = 10) -> List[Dict]:
        """
        Query recent trades
        
        Args:
            market_id: Optional market ID to filter trades
            first: Number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        where_clause = f'market: "{market_id}"' if market_id else ''
        
        query = f"""
        {{
          trades(
            first: {first}
            {', where: {' + where_clause + '}' if where_clause else ''}
            orderBy: timestamp
            orderDirection: desc
          ) {{
            id
            market {{
              id
              question
            }}
            outcome
            amount
            price
            timestamp
            trader
          }}
        }}
        """
        
        data = self._execute_query(query)
        
        if data and 'trades' in data:
            return data['trades']
        
        return []
    
    def get_market_statistics(self, market_id: str) -> Optional[Dict]:
        """
        Get comprehensive market statistics
        
        Args:
            market_id: Market identifier
            
        Returns:
            Dictionary with market stats
        """
        market = self.query_market(market_id)
        
        if not market:
            return None
        
        try:
            return {
                'market_id': market['id'],
                'question': market.get('question', ''),
                'volume_usd': float(market.get('volumeUSD', 0)),
                'liquidity': float(market.get('liquidityParameter', 0)),
                'active': market.get('active', False),
                'closed': market.get('closed', False),
                'outcomes': market.get('outcomes', []),
                'outcome_prices': [float(p) for p in market.get('outcomePrices', [])],
                'created_at': market.get('createdAt'),
                'updated_at': market.get('updatedAt'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error parsing market stats: {str(e)}")
            return None
    
    def search_markets_by_topic(self, topic: str, limit: int = 20) -> List[Dict]:
        """
        Search markets by topic keywords
        
        Args:
            topic: Topic to search for (e.g., "Bitcoin", "Election", "Sports")
            limit: Maximum results
            
        Returns:
            List of relevant markets
        """
        return self.query_markets(
            active=True,
            first=limit,
            question_contains=topic
        )
    
    def get_high_volume_markets(self, min_volume_usd: float = 10000, limit: int = 20) -> List[Dict]:
        """
        Get markets with high trading volume
        
        Args:
            min_volume_usd: Minimum volume threshold
            limit: Maximum results
            
        Returns:
            List of high-volume markets
        """
        markets = self.query_markets(active=True, first=limit)
        
        # Filter by volume (The Graph filtering is limited)
        return [
            market for market in markets
            if float(market.get('volumeUSD', 0)) >= min_volume_usd
        ]
    
    def health_check(self) -> bool:
        """
        Check if Subgraph API is accessible
        
        Returns:
            True if API is healthy
        """
        try:
            # Simple query to test connection
            query = '{ markets(first: 1) { id } }'
            data = self._execute_query(query)
            return data is not None and 'markets' in data
        except:
            return False
