"""
Polymarket Subgraph Client (The Graph)
- On-chain market data
- GraphQL queries
- Unlimited requests (decentralized)
"""

import requests
from typing import Dict, Optional, List, Any
from datetime import datetime


class PolymarketSubgraph:
    """Client for Polymarket Subgraph via The Graph"""
    
    def __init__(self):
        """Initialize Polymarket Subgraph client"""
        # Use The Graph's hosted service for Polymarket
        # Note: The actual endpoint may vary; this is a placeholder
        self.endpoint = "https://api.thegraph.com/subgraphs/name/polymarket/polymarket"
        
        # Fallback to Polymarket's direct API
        self.fallback_api = "https://clob.polymarket.com"
        
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """
        Execute a GraphQL query against the subgraph
        
        Args:
            query: GraphQL query string
            variables: Query variables dictionary
            
        Returns:
            Query result data, or None on error
        """
        try:
            payload = {'query': query}
            if variables:
                payload['variables'] = variables
            
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'errors' in data:
                print(f"GraphQL errors: {data['errors']}")
                return None
            
            return data.get('data')
            
        except Exception as e:
            print(f"Error executing GraphQL query: {e}")
            return None
    
    def query_markets(self, filters: Optional[Dict] = None, 
                     limit: int = 100) -> Optional[List[Dict]]:
        """
        Query active markets with filters
        
        Args:
            filters: Dictionary of filter criteria (e.g., {'active': True})
            limit: Maximum number of markets to return
            
        Returns:
            List of market dictionaries, or None on error
        """
        # For now, use the REST API as a fallback since subgraph endpoint may vary
        try:
            url = f"{self.fallback_api}/markets"
            params = {'limit': limit}
            
            if filters:
                if filters.get('active'):
                    params['active'] = 'true'
                if filters.get('closed'):
                    params['closed'] = 'true'
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse market data
            markets = []
            if isinstance(data, list):
                for market in data[:limit]:
                    markets.append(self._parse_market(market))
            
            return markets
            
        except Exception as e:
            print(f"Error querying markets: {e}")
            return None
    
    def get_market(self, market_id: str) -> Optional[Dict]:
        """
        Get specific market by ID
        
        Args:
            market_id: Market identifier
            
        Returns:
            Market data dictionary, or None on error
        """
        try:
            url = f"{self.fallback_api}/markets/{market_id}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_market(data)
            
        except Exception as e:
            print(f"Error fetching market {market_id}: {e}")
            return None
    
    def get_market_trades(self, market_id: str, limit: int = 100) -> Optional[List[Dict]]:
        """
        Get trade history for a market
        
        Args:
            market_id: Market identifier
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries, or None on error
        """
        try:
            url = f"{self.fallback_api}/markets/{market_id}/trades"
            params = {'limit': limit}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse trades
            trades = []
            if isinstance(data, list):
                for trade in data[:limit]:
                    trades.append({
                        'id': trade.get('id'),
                        'market_id': market_id,
                        'outcome': trade.get('outcome'),
                        'price': float(trade.get('price', 0)),
                        'amount': float(trade.get('amount', 0)),
                        'side': trade.get('side'),
                        'timestamp': trade.get('timestamp'),
                        'maker': trade.get('maker'),
                        'taker': trade.get('taker')
                    })
            
            return trades
            
        except Exception as e:
            print(f"Error fetching trades for market {market_id}: {e}")
            return None
    
    def get_market_prices(self, market_id: str) -> Optional[Dict]:
        """
        Get current prices for a market
        
        Args:
            market_id: Market identifier
            
        Returns:
            Dictionary with YES and NO prices, or None on error
        """
        try:
            url = f"{self.fallback_api}/markets/{market_id}/prices"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'market_id': market_id,
                'yes_price': float(data.get('yes', 0)),
                'no_price': float(data.get('no', 0)),
                'last_updated': data.get('timestamp', datetime.now().isoformat())
            }
            
        except Exception as e:
            print(f"Error fetching prices for market {market_id}: {e}")
            return None
    
    def get_market_liquidity(self, market_id: str) -> Optional[Dict]:
        """
        Get liquidity data for a market
        
        Args:
            market_id: Market identifier
            
        Returns:
            Liquidity data dictionary, or None on error
        """
        try:
            # This would use the order book endpoint
            url = f"{self.fallback_api}/markets/{market_id}/book"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate total liquidity from order book
            total_yes_liquidity = sum(float(order.get('size', 0)) 
                                     for order in data.get('bids', []))
            total_no_liquidity = sum(float(order.get('size', 0)) 
                                    for order in data.get('asks', []))
            
            return {
                'market_id': market_id,
                'yes_liquidity': total_yes_liquidity,
                'no_liquidity': total_no_liquidity,
                'total_liquidity': total_yes_liquidity + total_no_liquidity,
                'bid_count': len(data.get('bids', [])),
                'ask_count': len(data.get('asks', []))
            }
            
        except Exception as e:
            print(f"Error fetching liquidity for market {market_id}: {e}")
            return None
    
    def get_active_markets_with_volume(self, min_volume: float = 1000, 
                                       limit: int = 50) -> Optional[List[Dict]]:
        """
        Get active markets filtered by minimum volume
        
        Args:
            min_volume: Minimum 24h volume in USD
            limit: Maximum number of markets to return
            
        Returns:
            List of high-volume market dictionaries, or None on error
        """
        markets = self.query_markets(filters={'active': True}, limit=limit * 2)
        
        if not markets:
            return None
        
        # Filter by volume
        high_volume_markets = [
            m for m in markets 
            if m.get('volume_24h', 0) >= min_volume
        ]
        
        # Sort by volume descending
        high_volume_markets.sort(key=lambda x: x.get('volume_24h', 0), reverse=True)
        
        return high_volume_markets[:limit]
    
    def _parse_market(self, raw_market: Dict) -> Dict:
        """
        Parse raw market data into standardized format
        
        Args:
            raw_market: Raw market data from API
            
        Returns:
            Parsed market dictionary
        """
        return {
            'id': raw_market.get('id'),
            'question': raw_market.get('question', raw_market.get('title', '')),
            'description': raw_market.get('description', ''),
            'outcomes': raw_market.get('outcomes', ['YES', 'NO']),
            'active': raw_market.get('active', True),
            'closed': raw_market.get('closed', False),
            'volume_24h': float(raw_market.get('volume24hr', raw_market.get('volume', 0))),
            'liquidity': float(raw_market.get('liquidity', 0)),
            'yes_price': float(raw_market.get('outcomePrices', [0.5, 0.5])[0]),
            'no_price': float(raw_market.get('outcomePrices', [0.5, 0.5])[1]),
            'end_date': raw_market.get('endDate', raw_market.get('end_date')),
            'category': raw_market.get('category', 'Unknown'),
            'tags': raw_market.get('tags', [])
        }
    
    def search_markets(self, query: str, limit: int = 20) -> Optional[List[Dict]]:
        """
        Search markets by keyword
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching markets, or None on error
        """
        markets = self.query_markets(filters={'active': True}, limit=100)
        
        if not markets:
            return None
        
        # Simple text search in question and description
        query_lower = query.lower()
        matching_markets = [
            m for m in markets
            if query_lower in m.get('question', '').lower() or
               query_lower in m.get('description', '').lower()
        ]
        
        return matching_markets[:limit]
