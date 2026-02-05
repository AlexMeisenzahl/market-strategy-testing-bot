"""
Detector Module - Arbitrage opportunity detection

Identifies arbitrage opportunities where YES + NO < $1.00
Validates opportunities meet minimum profit thresholds
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from logger import get_logger


class ArbitrageOpportunity:
    """Represents a single arbitrage opportunity"""
    
    def __init__(self, market_id: str, market_name: str, 
                 yes_price: float, no_price: float):
        """
        Initialize arbitrage opportunity
        
        Args:
            market_id: Unique market identifier
            market_name: Human-readable market name
            yes_price: Price of YES contract
            no_price: Price of NO contract
        """
        self.market_id = market_id
        self.market_name = market_name
        self.yes_price = yes_price
        self.no_price = no_price
        self.price_sum = yes_price + no_price
        self.detected_at = datetime.now()
    
    @property
    def profit_margin(self) -> float:
        """Calculate profit margin as percentage"""
        if self.price_sum == 0:
            return 0.0
        return ((1.0 - self.price_sum) / self.price_sum) * 100
    
    @property
    def expected_profit(self) -> float:
        """Calculate expected profit per $1 invested"""
        return 1.0 - self.price_sum
    
    def calculate_profit_for_amount(self, amount: float) -> float:
        """
        Calculate expected profit for a given investment amount
        
        Args:
            amount: Investment amount in USD
            
        Returns:
            Expected profit in USD
        """
        # When you buy both YES and NO for 'amount' each
        # Total cost is amount * (yes_price + no_price)
        # Return is always 'amount' (since one side pays out)
        # Profit is return - cost
        total_cost = amount * self.price_sum
        return amount - total_cost
    
    def is_valid(self) -> bool:
        """Check if opportunity is still valid (not stale)"""
        # Opportunity is valid if detected within last 30 seconds
        age = (datetime.now() - self.detected_at).total_seconds()
        return age < 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'market_id': self.market_id,
            'market_name': self.market_name,
            'yes_price': self.yes_price,
            'no_price': self.no_price,
            'price_sum': self.price_sum,
            'profit_margin': self.profit_margin,
            'detected_at': self.detected_at.isoformat()
        }


class ArbitrageDetector:
    """Detect arbitrage opportunities in market prices"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize arbitrage detector
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Detection thresholds
        self.min_profit_margin = config.get('min_profit_margin', 0.02)  # 2%
        self.max_trade_size = config.get('max_trade_size', 10)
        
        # Track opportunities found
        self.opportunities_found = 0
        self.total_expected_profit = 0.0
    
    def find_arbitrage_opportunities(self, markets: List[Dict[str, Any]],
                                    prices_dict: Dict[str, Dict[str, float]]) -> List[ArbitrageOpportunity]:
        """
        Find arbitrage opportunities from market prices
        
        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data
            
        Returns:
            List of valid arbitrage opportunities
        """
        opportunities = []
        
        for market in markets:
            market_id = market.get('id', market.get('market_id', 'unknown'))
            market_name = market.get('question', market.get('name', market_id))
            
            # Get prices for this market
            prices = prices_dict.get(market_id)
            if not prices:
                continue
            
            yes_price = prices.get('yes', 0)
            no_price = prices.get('no', 0)
            
            # Validate prices
            if not self._validate_prices(yes_price, no_price):
                continue
            
            # Check if arbitrage opportunity exists
            if self._is_arbitrage_opportunity(yes_price, no_price):
                opportunity = ArbitrageOpportunity(
                    market_id=market_id,
                    market_name=market_name,
                    yes_price=yes_price,
                    no_price=no_price
                )
                
                # Check if meets minimum profit threshold
                if opportunity.profit_margin >= (self.min_profit_margin * 100):
                    opportunities.append(opportunity)
                    self.opportunities_found += 1
                    
                    # Log the opportunity
                    self.logger.log_opportunity(
                        market=market_name,
                        yes_price=yes_price,
                        no_price=no_price,
                        action_taken="detected"
                    )
                else:
                    # Log opportunity but mark as skipped
                    self.logger.log_opportunity(
                        market=market_name,
                        yes_price=yes_price,
                        no_price=no_price,
                        action_taken=f"skipped_low_profit_{opportunity.profit_margin:.1f}%"
                    )
        
        return opportunities
    
    def _validate_prices(self, yes_price: float, no_price: float) -> bool:
        """
        Validate that prices are reasonable
        
        Args:
            yes_price: YES contract price
            no_price: NO contract price
            
        Returns:
            True if prices are valid
        """
        # Prices should be between 0 and 1
        if yes_price <= 0 or yes_price >= 1:
            return False
        if no_price <= 0 or no_price >= 1:
            return False
        
        # Sum should be positive
        if yes_price + no_price <= 0:
            return False
        
        return True
    
    def _is_arbitrage_opportunity(self, yes_price: float, no_price: float) -> bool:
        """
        Check if prices represent an arbitrage opportunity
        
        Args:
            yes_price: YES contract price
            no_price: NO contract price
            
        Returns:
            True if arbitrage opportunity exists
        """
        # Arbitrage exists when YES + NO < $1.00
        price_sum = yes_price + no_price
        return price_sum < 1.0
    
    def check_liquidity(self, market_data: Dict[str, Any]) -> bool:
        """
        Check if market has sufficient liquidity for trade
        
        Args:
            market_data: Market data including liquidity info
            
        Returns:
            True if sufficient liquidity exists
        """
        # For paper trading, we assume sufficient liquidity
        # In production, check orderbook depth
        return True
    
    def estimate_slippage(self, opportunity: ArbitrageOpportunity,
                         trade_size: float) -> float:
        """
        Estimate price slippage for a given trade size
        
        Args:
            opportunity: Arbitrage opportunity
            trade_size: Size of trade in USD
            
        Returns:
            Estimated slippage as decimal (e.g., 0.01 = 1%)
        """
        # For paper trading, assume minimal slippage
        # In production, calculate based on orderbook depth
        return 0.001  # 0.1% slippage
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detection statistics for dashboard
        
        Returns:
            Dictionary with detection statistics
        """
        return {
            'opportunities_found': self.opportunities_found,
            'total_expected_profit': self.total_expected_profit
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters"""
        self.opportunities_found = 0
        self.total_expected_profit = 0.0
