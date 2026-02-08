"""
Arbitrage Strategy Module

Implements the classic arbitrage strategy where YES + NO < $1.00 creates
a risk-free profit opportunity. This is the original strategy used by the bot.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
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
        self.opportunity_type = "arbitrage"
    
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
        total_cost = amount * self.price_sum
        return amount - total_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'market_id': self.market_id,
            'market_name': self.market_name,
            'yes_price': self.yes_price,
            'no_price': self.no_price,
            'price_sum': self.price_sum,
            'profit_margin': self.profit_margin,
            'opportunity_type': self.opportunity_type,
            'arbitrage_type': getattr(self, 'arbitrage_type', 'Simple'),
            'detected_at': self.detected_at.isoformat()
        }


class ArbitrageStrategy:
    """
    Classic arbitrage strategy: Buy YES + NO when sum < $1.00
    
    This is a risk-free strategy that profits from pricing inefficiencies
    where the combined price of YES and NO contracts is less than their
    guaranteed $1.00 payout.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize arbitrage strategy
        
        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.logger = get_logger()
        self.strategy_name = "polymarket_arbitrage"
        
        # Strategy parameters
        self.min_profit_margin = config.get('min_profit_margin', 0.02)  # 2%
        self.max_trade_size = config.get('max_trade_size', 10)
        self.max_price_sum = config.get('max_price_sum', 0.98)  # Only consider if sum < 0.98
        
        # Arbitrage types configuration
        self.arbitrage_types_config = config.get('arbitrage_types', {})
        
        # Statistics tracking
        self.opportunities_found = 0
        self.opportunities_taken = 0
        self.total_expected_profit = 0.0
        self.total_actual_profit = 0.0
        
        # Active positions (market_id -> position info)
        self.active_positions: Dict[str, Dict[str, Any]] = {}
    
    def analyze(self, market_data: Dict[str, Any], 
                price_data: Dict[str, float]) -> Optional[ArbitrageOpportunity]:
        """
        Analyze a market for arbitrage opportunities
        
        Args:
            market_data: Market information (id, name, etc.)
            price_data: Current prices {'yes': float, 'no': float}
            
        Returns:
            ArbitrageOpportunity if found, None otherwise
        """
        market_id = market_data.get('id', market_data.get('market_id', 'unknown'))
        market_name = market_data.get('question', market_data.get('name', market_id))
        
        yes_price = price_data.get('yes', 0)
        no_price = price_data.get('no', 0)
        
        # Validate prices
        if not self._validate_prices(yes_price, no_price):
            return None
        
        # Check if arbitrage opportunity exists
        if not self._is_arbitrage_opportunity(yes_price, no_price):
            return None
        
        # Create opportunity object
        opportunity = ArbitrageOpportunity(
            market_id=market_id,
            market_name=market_name,
            yes_price=yes_price,
            no_price=no_price
        )
        
        # Check if meets minimum profit threshold
        if opportunity.profit_margin >= (self.min_profit_margin * 100):
            self.opportunities_found += 1
            
            # Log the opportunity
            self.logger.log_opportunity(
                market=market_name,
                yes_price=yes_price,
                no_price=no_price,
                action_taken=f"{self.strategy_name}_detected"
            )
            
            return opportunity
        
        return None
    
    def find_opportunities(self, markets: List[Dict[str, Any]],
                          prices_dict: Dict[str, Dict[str, float]]) -> List[ArbitrageOpportunity]:
        """
        Find all arbitrage opportunities across multiple markets
        
        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data
            
        Returns:
            List of valid arbitrage opportunities
        """
        opportunities = []
        
        for market in markets:
            market_id = market.get('id', market.get('market_id', 'unknown'))
            prices = prices_dict.get(market_id)
            
            if not prices:
                continue
            
            opportunity = self.analyze(market, prices)
            if opportunity:
                opportunities.append(opportunity)
        
        return opportunities
    
    def should_enter(self, opportunity: ArbitrageOpportunity) -> bool:
        """
        Determine if we should enter a position on this opportunity
        
        Args:
            opportunity: ArbitrageOpportunity to evaluate
            
        Returns:
            True if should enter position, False otherwise
        """
        # Don't enter if we already have a position in this market
        if opportunity.market_id in self.active_positions:
            return False
        
        # Check profit margin meets threshold
        if opportunity.profit_margin < (self.min_profit_margin * 100):
            return False
        
        # Check price sum is reasonable
        if opportunity.price_sum >= self.max_price_sum:
            return False
        
        # Additional checks could include:
        # - Liquidity check
        # - Market expiry check
        # - Risk limits check
        
        return True
    
    def should_exit(self, market_id: str, current_prices: Dict[str, float]) -> bool:
        """
        Determine if we should exit a position
        
        For arbitrage strategy, we typically hold to expiry since it's risk-free.
        However, we might exit early if prices improve significantly.
        
        Args:
            market_id: Market identifier
            current_prices: Current market prices
            
        Returns:
            True if should exit position, False otherwise
        """
        # Check if we have an active position
        if market_id not in self.active_positions:
            return False
        
        position = self.active_positions[market_id]
        entry_sum = position['entry_price_sum']
        
        yes_price = current_prices.get('yes', 0)
        no_price = current_prices.get('no', 0)
        current_sum = yes_price + no_price
        
        # Exit if prices have improved significantly (can lock in profit early)
        # For example, if price sum has increased by 5% or more
        improvement_threshold = 0.05
        if current_sum >= entry_sum * (1 + improvement_threshold):
            return True
        
        # Exit if market is about to expire (would be checked via market data)
        # This would require additional market metadata
        
        return False
    
    def enter_position(self, opportunity: ArbitrageOpportunity, 
                       trade_size: float) -> Dict[str, Any]:
        """
        Enter a position on an arbitrage opportunity
        
        Args:
            opportunity: ArbitrageOpportunity to trade
            trade_size: Amount to invest in USD
            
        Returns:
            Position information dictionary
        """
        # Calculate expected profit
        expected_profit = opportunity.calculate_profit_for_amount(trade_size)
        
        # Record position
        position = {
            'market_id': opportunity.market_id,
            'market_name': opportunity.market_name,
            'entry_time': datetime.now(),
            'entry_price_sum': opportunity.price_sum,
            'yes_price': opportunity.yes_price,
            'no_price': opportunity.no_price,
            'trade_size': trade_size,
            'expected_profit': expected_profit,
            'status': 'active'
        }
        
        self.active_positions[opportunity.market_id] = position
        self.opportunities_taken += 1
        self.total_expected_profit += expected_profit
        
        # Log the trade
        self.logger.log_trade(
            market=opportunity.market_name,
            yes_price=opportunity.yes_price,
            no_price=opportunity.no_price,
            profit_usd=expected_profit,
            status=f"{self.strategy_name}_entered"
        )
        
        return position
    
    def exit_position(self, market_id: str, exit_prices: Dict[str, float],
                     reason: str = "manual") -> Dict[str, Any]:
        """
        Exit a position
        
        Args:
            market_id: Market identifier
            exit_prices: Exit prices {'yes': float, 'no': float}
            reason: Reason for exit (profit_target, stop_loss, manual, etc.)
            
        Returns:
            Exit information dictionary
        """
        if market_id not in self.active_positions:
            return {'error': 'No active position found'}
        
        position = self.active_positions[market_id]
        
        # Calculate actual profit based on exit prices
        entry_sum = position['entry_price_sum']
        exit_sum = exit_prices['yes'] + exit_prices['no']
        trade_size = position['trade_size']
        
        # Profit improvement from entry to exit
        actual_profit = trade_size * (exit_sum - entry_sum) + position['expected_profit']
        
        # Update statistics
        self.total_actual_profit += actual_profit
        
        # Log the exit
        self.logger.log_trade(
            market=position['market_name'],
            yes_price=exit_prices['yes'],
            no_price=exit_prices['no'],
            profit_usd=actual_profit,
            status=f"{self.strategy_name}_exited_{reason}"
        )
        
        # Create exit record
        exit_info = {
            'market_id': market_id,
            'market_name': position['market_name'],
            'exit_time': datetime.now(),
            'exit_prices': exit_prices,
            'entry_sum': entry_sum,
            'exit_sum': exit_sum,
            'expected_profit': position['expected_profit'],
            'actual_profit': actual_profit,
            'reason': reason
        }
        
        # Remove from active positions
        del self.active_positions[market_id]
        
        return exit_info
    
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
        price_sum = yes_price + no_price
        return price_sum < 1.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get strategy statistics
        
        Returns:
            Dictionary with strategy statistics
        """
        # Calculate execution rate (percentage of opportunities that were traded)
        if self.opportunities_found > 0:
            execution_rate = (self.opportunities_taken / self.opportunities_found) * 100
        else:
            execution_rate = 0.0
        
        return {
            'strategy_name': self.strategy_name,
            'opportunities_found': self.opportunities_found,
            'opportunities_taken': self.opportunities_taken,
            'total_expected_profit': self.total_expected_profit,
            'total_actual_profit': self.total_actual_profit,
            'active_positions': len(self.active_positions),
            'execution_rate': execution_rate
        }
    
    def reset_statistics(self) -> None:
        """Reset strategy statistics"""
        self.opportunities_found = 0
        self.opportunities_taken = 0
        self.total_expected_profit = 0.0
        self.total_actual_profit = 0.0
    
    def get_name(self) -> str:
        """
        Get strategy name
        
        Returns:
            Strategy name string
        """
        return self.strategy_name
