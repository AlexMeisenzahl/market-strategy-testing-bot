"""
Polymarket Subgraph Client - GraphQL API for On-Chain Polymarket Data

Provides:
- All Polymarket prediction markets (on-chain data)
- Market trades, volumes, and statistics
- Unlimited requests (decentralized via The Graph)
- Used by Polymarket.com frontend itself

No API keys required.
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Any


class PolymarketSubgraph:
    """Polymarket Subgraph Client via The Graph"""
    
    # The Graph subgraph endpoint for Polymarket
    SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/tokenunion/polymarket"
    
    # Alternative: Direct Polymarket API (public, no auth)
    POLYMARKET_API = "https://clob.polymarket.com"
    
    def __init__(self, use_subgraph: bool = True):
        """
        Initialize Polymarket Subgraph client
        
        Args:
            use_subgraph: If True, use The Graph subgraph. If False, use Polymarket API
        """
        self.use_subgraph = use_subgraph
        self.cache: Dict[str, Any] = {}
    
    def get_markets(
        self,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get list of Polymarket markets
        
        Args:
            active_only: Only return active markets
            limit: Maximum number of markets to return
        
        Returns:
            List of market dictionaries
        """
        if self.use_subgraph:
            return self._get_markets_subgraph(active_only, limit)
        else:
            return self._get_markets_api(active_only, limit)
    
    def _get_markets_api(
        self,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get markets via Polymarket API"""
        try:
            params = {
                'limit': limit,
                'offset': 0
            }
            
            if active_only:
                params['active'] = 'true'
            
            response = requests.get(
                f"{self.POLYMARKET_API}/markets",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                markets = response.json()
                
                # Normalize market format
                normalized = []
                for market in markets:
                    normalized.append({
                        'id': market.get('condition_id'),
                        'question': market.get('question'),
                        'description': market.get('description', ''),
                        'end_date': market.get('end_date_iso'),
                        'active': market.get('active', True),
                        'volume': float(market.get('volume', 0)),
                        'liquidity': float(market.get('liquidity', 0)),
                        'outcomes': market.get('outcomes', ['YES', 'NO'])
                    })
                
                return normalized
        
        except Exception as e:
            print(f"Polymarket API error: {e}")
        
        return []
    
    def _get_markets_subgraph(
        self,
        active_only: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get markets via The Graph subgraph"""
        query = """
        query GetMarkets($limit: Int!, $activeOnly: Boolean!) {
            markets(
                first: $limit,
                orderBy: volume,
                orderDirection: desc,
                where: { active: $activeOnly }
            ) {
                id
                question
                description
                endDate
                active
                volume
                liquidity
                outcomes
                createdAt
            }
        }
        """
        
        variables = {
            'limit': limit,
            'activeOnly': active_only
        }
        
        try:
            response = requests.post(
                self.SUBGRAPH_URL,
                json={'query': query, 'variables': variables},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('data', {}).get('markets', [])
                
                # Normalize format
                normalized = []
                for market in markets:
                    normalized.append({
                        'id': market['id'],
                        'question': market.get('question', ''),
                        'description': market.get('description', ''),
                        'end_date': datetime.fromtimestamp(int(market.get('endDate', 0))),
                        'active': market.get('active', True),
                        'volume': float(market.get('volume', 0)),
                        'liquidity': float(market.get('liquidity', 0)),
                        'outcomes': market.get('outcomes', ['YES', 'NO']),
                        'created_at': datetime.fromtimestamp(int(market.get('createdAt', 0)))
                    })
                
                return normalized
        
        except Exception as e:
            print(f"Subgraph query error: {e}")
        
        return []
    
    def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific market
        
        Args:
            market_id: Market condition ID
        
        Returns:
            Market dictionary or None
        """
        # Check cache
        if market_id in self.cache:
            return self.cache[market_id]
        
        if self.use_subgraph:
            return self._get_market_subgraph(market_id)
        else:
            return self._get_market_api(market_id)
    
    def _get_market_api(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get market via Polymarket API"""
        try:
            response = requests.get(
                f"{self.POLYMARKET_API}/markets/{market_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                market = response.json()
                
                normalized = {
                    'id': market.get('condition_id'),
                    'question': market.get('question'),
                    'description': market.get('description', ''),
                    'end_date': market.get('end_date_iso'),
                    'active': market.get('active', True),
                    'volume': float(market.get('volume', 0)),
                    'liquidity': float(market.get('liquidity', 0)),
                    'outcomes': market.get('outcomes', ['YES', 'NO'])
                }
                
                # Cache it
                self.cache[market_id] = normalized
                
                return normalized
        
        except Exception as e:
            print(f"Polymarket API error for market {market_id}: {e}")
        
        return None
    
    def _get_market_subgraph(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get market via The Graph subgraph"""
        query = """
        query GetMarket($marketId: ID!) {
            market(id: $marketId) {
                id
                question
                description
                endDate
                active
                volume
                liquidity
                outcomes
                createdAt
            }
        }
        """
        
        try:
            response = requests.post(
                self.SUBGRAPH_URL,
                json={'query': query, 'variables': {'marketId': market_id}},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                market = data.get('data', {}).get('market')
                
                if market:
                    normalized = {
                        'id': market['id'],
                        'question': market.get('question', ''),
                        'description': market.get('description', ''),
                        'end_date': datetime.fromtimestamp(int(market.get('endDate', 0))),
                        'active': market.get('active', True),
                        'volume': float(market.get('volume', 0)),
                        'liquidity': float(market.get('liquidity', 0)),
                        'outcomes': market.get('outcomes', ['YES', 'NO']),
                        'created_at': datetime.fromtimestamp(int(market.get('createdAt', 0)))
                    }
                    
                    # Cache it
                    self.cache[market_id] = normalized
                    
                    return normalized
        
        except Exception as e:
            print(f"Subgraph query error for market {market_id}: {e}")
        
        return None
    
    def get_market_prices(self, market_id: str) -> Optional[Dict[str, float]]:
        """
        Get current prices for a market
        
        Args:
            market_id: Market condition ID
        
        Returns:
            Dictionary with 'yes' and 'no' prices
        """
        try:
            # Use Polymarket API for real-time prices
            response = requests.get(
                f"{self.POLYMARKET_API}/prices",
                params={'market': market_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract YES and NO prices
                yes_price = None
                no_price = None
                
                if isinstance(data, dict):
                    yes_price = data.get('yes')
                    no_price = data.get('no')
                elif isinstance(data, list) and len(data) >= 2:
                    yes_price = data[0]
                    no_price = data[1]
                
                if yes_price is not None and no_price is not None:
                    return {
                        'yes': float(yes_price),
                        'no': float(no_price),
                        'market_id': market_id,
                        'timestamp': datetime.now().isoformat()
                    }
        
        except Exception as e:
            print(f"Price fetch error for market {market_id}: {e}")
        
        return None
    
    def get_market_trades(
        self,
        market_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades for a market
        
        Args:
            market_id: Market condition ID
            limit: Maximum number of trades to return
        
        Returns:
            List of trade dictionaries
        """
        if not self.use_subgraph:
            # API doesn't provide trade history easily
            return []
        
        query = """
        query GetTrades($marketId: ID!, $limit: Int!) {
            trades(
                first: $limit,
                orderBy: timestamp,
                orderDirection: desc,
                where: { market: $marketId }
            ) {
                id
                outcome
                price
                amount
                timestamp
                trader
            }
        }
        """
        
        try:
            response = requests.post(
                self.SUBGRAPH_URL,
                json={'query': query, 'variables': {'marketId': market_id, 'limit': limit}},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                trades = data.get('data', {}).get('trades', [])
                
                normalized = []
                for trade in trades:
                    normalized.append({
                        'id': trade['id'],
                        'outcome': trade.get('outcome'),
                        'price': float(trade.get('price', 0)),
                        'amount': float(trade.get('amount', 0)),
                        'timestamp': datetime.fromtimestamp(int(trade.get('timestamp', 0))),
                        'trader': trade.get('trader')
                    })
                
                return normalized
        
        except Exception as e:
            print(f"Trades query error for market {market_id}: {e}")
        
        return []
    
    def search_markets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for markets by question text
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of matching markets
        """
        # Get all markets and filter by query
        all_markets = self.get_markets(active_only=True, limit=limit * 2)
        
        query_lower = query.lower()
        matching_markets = [
            m for m in all_markets
            if query_lower in m['question'].lower()
        ]
        
        return matching_markets[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall Polymarket statistics
        
        Returns:
            Dictionary with platform statistics
        """
        markets = self.get_markets(active_only=False, limit=1000)
        
        if not markets:
            return {}
        
        active_markets = [m for m in markets if m['active']]
        total_volume = sum(m['volume'] for m in markets)
        total_liquidity = sum(m['liquidity'] for m in markets)
        
        return {
            'total_markets': len(markets),
            'active_markets': len(active_markets),
            'total_volume': total_volume,
            'total_liquidity': total_liquidity,
            'avg_volume_per_market': total_volume / len(markets) if markets else 0
        }
