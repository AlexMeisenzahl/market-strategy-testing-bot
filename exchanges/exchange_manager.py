"""
Exchange Manager

Coordinates multiple exchanges and provides unified market data access.
"""

from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class ExchangeManager:
    """
    Manages multiple exchange clients and aggregates data
    
    Fetches from all enabled exchanges in parallel and handles failures gracefully.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize exchange manager
        
        Args:
            config: Configuration dictionary with exchange settings
        """
        self.config = config
        self.exchanges = {}
        
        # Load exchange clients
        self._load_exchanges()
    
    def _load_exchanges(self) -> None:
        """Load all enabled exchange clients"""
        exchanges_config = self.config.get('exchanges', {})
        
        # Load Kalshi
        kalshi_config = exchanges_config.get('kalshi', {})
        if kalshi_config.get('enabled', False):
            try:
                from exchanges.kalshi_client import KalshiClient
                self.exchanges['kalshi'] = KalshiClient(kalshi_config)
                print("Loaded Kalshi exchange client")
            except Exception as e:
                print(f"Failed to load Kalshi client: {e}")
        
        # Note: Polymarket and PredictIt would be loaded here
        # For now, they're handled by existing code
    
    def get_all_markets(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch markets from all enabled exchanges in parallel
        
        Returns:
            Dictionary mapping exchange name to list of markets
        """
        results = {}
        
        if not self.exchanges:
            return results
        
        # Fetch in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(self.exchanges)) as executor:
            # Submit all fetch tasks
            future_to_exchange = {
                executor.submit(client.get_active_markets): name
                for name, client in self.exchanges.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_exchange):
                exchange_name = future_to_exchange[future]
                try:
                    markets = future.result(timeout=10)
                    results[exchange_name] = markets
                except Exception as e:
                    print(f"Error fetching from {exchange_name}: {e}")
                    results[exchange_name] = []
        
        return results
    
    def get_market_prices(self, exchange: str, market_id: str) -> Dict[str, float]:
        """
        Get prices for a specific market on a specific exchange
        
        Args:
            exchange: Exchange name
            market_id: Market identifier
            
        Returns:
            Dictionary with 'yes' and 'no' prices
        """
        if exchange not in self.exchanges:
            return {}
        
        try:
            return self.exchanges[exchange].get_market_prices(market_id) or {}
        except Exception as e:
            print(f"Error fetching prices from {exchange}: {e}")
            return {}
