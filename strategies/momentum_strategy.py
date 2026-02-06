"""
Momentum Strategy Module

Detects trending markets where price is moving strongly in one direction.
Enters when momentum is strong and confirmed by volume, exits on reversal
or profit targets.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
from logger import get_logger


class PriceHistory:
    """Track price history for momentum calculations"""
    
    def __init__(self, max_age_seconds: int = 3600):
        """
        Initialize price history tracker
        
        Args:
            max_age_seconds: Maximum age of data to keep (default: 1 hour)
        """
        self.prices: deque = deque()  # [(timestamp, yes_price, no_price, volume), ...]
        self.max_age_seconds = max_age_seconds
    
    def add_price(self, yes_price: float, no_price: float, 
                  volume: float = 0.0) -> None:
        """Add a new price data point"""
        self.prices.append((datetime.now(), yes_price, no_price, volume))
        self._clean_old_data()
    
    def _clean_old_data(self) -> None:
        """Remove data older than max_age_seconds"""
        cutoff_time = datetime.now() - timedelta(seconds=self.max_age_seconds)
        while self.prices and self.prices[0][0] < cutoff_time:
            self.prices.popleft()
    
    def get_prices_in_window(self, window_seconds: int) -> List[Tuple]:
        """
        Get prices within a time window
        
        Args:
            window_seconds: Time window in seconds
            
        Returns:
            List of (timestamp, yes_price, no_price, volume) tuples
        """
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        return [p for p in self.prices if p[0] >= cutoff_time]
    
    def calculate_price_change(self, window_seconds: int) -> float:
        """
        Calculate price change percentage over time window
        
        Args:
            window_seconds: Time window in seconds
            
        Returns:
            Price change as percentage (positive = upward momentum)
        """
        prices = self.get_prices_in_window(window_seconds)
        if len(prices) < 2:
            return 0.0
        
        # Use YES price as the primary indicator
        oldest_price = prices[0][1]
        newest_price = prices[-1][1]
        
        if oldest_price == 0:
            return 0.0
        
        change_pct = ((newest_price - oldest_price) / oldest_price) * 100
        return change_pct
    
    def calculate_volume_change(self, window_seconds: int) -> float:
        """
        Calculate volume change over time window
        
        Args:
            window_seconds: Time window in seconds
            
        Returns:
            Volume change as percentage
        """
        prices = self.get_prices_in_window(window_seconds)
        if len(prices) < 2:
            return 0.0
        
        # Calculate average volume in first half vs second half
        mid_point = len(prices) // 2
        if mid_point == 0:
            return 0.0
        
        first_half_volume = sum(p[3] for p in prices[:mid_point]) / mid_point
        second_half_volume = sum(p[3] for p in prices[mid_point:]) / (len(prices) - mid_point)
        
        if first_half_volume == 0:
            return 0.0
        
        volume_change = ((second_half_volume - first_half_volume) / first_half_volume) * 100
        return volume_change


class MomentumOpportunity:
    """Represents a momentum trading opportunity"""
    
    def __init__(self, market_id: str, market_name: str,
                 direction: str, momentum_score: float,
                 current_price: float, price_change_5m: float,
                 price_change_15m: float, volume_change: float):
        """
        Initialize momentum opportunity
        
        Args:
            market_id: Unique market identifier
            market_name: Human-readable market name
            direction: 'bullish' or 'bearish'
            momentum_score: Overall momentum score (0-100)
            current_price: Current YES price
            price_change_5m: Price change over 5 minutes (%)
            price_change_15m: Price change over 15 minutes (%)
            volume_change: Volume change (%)
        """
        self.market_id = market_id
        self.market_name = market_name
        self.direction = direction
        self.momentum_score = momentum_score
        self.current_price = current_price
        self.price_change_5m = price_change_5m
        self.price_change_15m = price_change_15m
        self.volume_change = volume_change
        self.detected_at = datetime.now()
        self.opportunity_type = "momentum"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'market_id': self.market_id,
            'market_name': self.market_name,
            'direction': self.direction,
            'momentum_score': self.momentum_score,
            'current_price': self.current_price,
            'price_change_5m': self.price_change_5m,
            'price_change_15m': self.price_change_15m,
            'volume_change': self.volume_change,
            'opportunity_type': self.opportunity_type,
            'detected_at': self.detected_at.isoformat()
        }


class MomentumStrategy:
    """
    Momentum-based trading strategy
    
    Detects markets with strong price trends and enters positions
    in the direction of momentum. Exits on reversal signals or
    profit targets.
    
    Entry Criteria:
    - Price moved >2% in 5 minutes
    - Volume up >50% vs average
    - Momentum score >70
    
    Exit Criteria:
    - Price reversed >1%
    - Momentum score <40
    - Profit target hit (+10-30%)
    - Stop loss (-10%)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize momentum strategy
        
        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.logger = get_logger()
        self.strategy_name = "momentum"
        
        # Strategy parameters
        self.min_price_change_5m = config.get('momentum_min_price_change_5m', 2.0)  # 2%
        self.min_volume_change = config.get('momentum_min_volume_change', 50.0)  # 50%
        self.min_momentum_score = config.get('momentum_min_score', 70.0)
        self.exit_momentum_score = config.get('momentum_exit_score', 40.0)
        self.profit_target_min = config.get('momentum_profit_target_min', 10.0)  # 10%
        self.profit_target_max = config.get('momentum_profit_target_max', 30.0)  # 30%
        self.stop_loss_pct = config.get('momentum_stop_loss', 10.0)  # 10%
        self.reversal_threshold = config.get('momentum_reversal_threshold', 1.0)  # 1%
        
        # Price history tracking (market_id -> PriceHistory)
        self.price_history: Dict[str, PriceHistory] = {}
        
        # Statistics tracking
        self.opportunities_found = 0
        self.opportunities_taken = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        
        # Active positions (market_id -> position info)
        self.active_positions: Dict[str, Dict[str, Any]] = {}
    
    def update_price_history(self, market_id: str, yes_price: float,
                            no_price: float, volume: float = 0.0) -> None:
        """
        Update price history for a market
        
        Args:
            market_id: Market identifier
            yes_price: Current YES price
            no_price: Current NO price
            volume: Current volume (if available)
        """
        if market_id not in self.price_history:
            self.price_history[market_id] = PriceHistory()
        
        self.price_history[market_id].add_price(yes_price, no_price, volume)
    
    def calculate_momentum_score(self, market_id: str) -> Tuple[float, Dict[str, float]]:
        """
        Calculate momentum score for a market
        
        Args:
            market_id: Market identifier
            
        Returns:
            Tuple of (momentum_score, metrics_dict)
        """
        if market_id not in self.price_history:
            return 0.0, {}
        
        history = self.price_history[market_id]
        
        # Calculate price changes over different windows
        price_change_5m = history.calculate_price_change(300)  # 5 minutes
        price_change_15m = history.calculate_price_change(900)  # 15 minutes
        price_change_1h = history.calculate_price_change(3600)  # 1 hour
        
        # Calculate volume change
        volume_change = history.calculate_volume_change(300)  # 5 minutes
        
        # Calculate acceleration (is momentum increasing?)
        acceleration = 0.0
        if price_change_15m != 0:
            # If 5m change is larger than 15m average, momentum is accelerating
            acceleration = (abs(price_change_5m) / (abs(price_change_15m) / 3)) - 1.0
            acceleration = max(-1.0, min(1.0, acceleration))  # Clamp to [-1, 1]
        
        # Calculate momentum score (0-100)
        # Weight: 40% recent price change, 30% volume, 30% acceleration
        score = 0.0
        
        # Price change component (0-40 points)
        price_score = min(40, abs(price_change_5m) * 10)
        score += price_score
        
        # Volume component (0-30 points)
        volume_score = min(30, (volume_change / 100) * 30)
        score += volume_score
        
        # Acceleration component (0-30 points)
        accel_score = (acceleration + 1.0) * 15  # Map [-1,1] to [0,30]
        score += accel_score
        
        metrics = {
            'price_change_5m': price_change_5m,
            'price_change_15m': price_change_15m,
            'price_change_1h': price_change_1h,
            'volume_change': volume_change,
            'acceleration': acceleration,
            'momentum_score': score
        }
        
        return score, metrics
    
    def analyze(self, market_data: Dict[str, Any],
                price_data: Dict[str, float]) -> Optional[MomentumOpportunity]:
        """
        Analyze a market for momentum opportunities
        
        Args:
            market_data: Market information (id, name, etc.)
            price_data: Current prices {'yes': float, 'no': float, 'volume': float}
            
        Returns:
            MomentumOpportunity if found, None otherwise
        """
        market_id = market_data.get('id', market_data.get('market_id', 'unknown'))
        market_name = market_data.get('question', market_data.get('name', market_id))
        
        yes_price = price_data.get('yes', 0)
        no_price = price_data.get('no', 0)
        volume = price_data.get('volume', 0)
        
        # Update price history
        self.update_price_history(market_id, yes_price, no_price, volume)
        
        # Calculate momentum score
        momentum_score, metrics = self.calculate_momentum_score(market_id)
        
        # Check entry criteria
        if not self._meets_entry_criteria(metrics, momentum_score):
            return None
        
        # Determine direction
        direction = 'bullish' if metrics['price_change_5m'] > 0 else 'bearish'
        
        # Create opportunity
        opportunity = MomentumOpportunity(
            market_id=market_id,
            market_name=market_name,
            direction=direction,
            momentum_score=momentum_score,
            current_price=yes_price,
            price_change_5m=metrics['price_change_5m'],
            price_change_15m=metrics['price_change_15m'],
            volume_change=metrics['volume_change']
        )
        
        self.opportunities_found += 1
        
        # Log the opportunity
        self.logger.log_opportunity(
            market=market_name,
            yes_price=yes_price,
            no_price=no_price,
            action_taken=f"{self.strategy_name}_detected_{direction}"
        )
        
        return opportunity
    
    def find_opportunities(self, markets: List[Dict[str, Any]],
                          prices_dict: Dict[str, Dict[str, float]]) -> List[MomentumOpportunity]:
        """
        Find all momentum opportunities across multiple markets
        
        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data
            
        Returns:
            List of valid momentum opportunities
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
    
    def should_enter(self, opportunity: MomentumOpportunity) -> bool:
        """
        Determine if we should enter a position on this opportunity
        
        Args:
            opportunity: MomentumOpportunity to evaluate
            
        Returns:
            True if should enter position, False otherwise
        """
        # Don't enter if we already have a position in this market
        if opportunity.market_id in self.active_positions:
            return False
        
        # Check momentum score meets threshold
        if opportunity.momentum_score < self.min_momentum_score:
            return False
        
        # Check price change meets threshold
        if abs(opportunity.price_change_5m) < self.min_price_change_5m:
            return False
        
        # Check volume change meets threshold
        if opportunity.volume_change < self.min_volume_change:
            return False
        
        return True
    
    def should_exit(self, market_id: str, current_prices: Dict[str, float]) -> Tuple[bool, str]:
        """
        Determine if we should exit a position
        
        Args:
            market_id: Market identifier
            current_prices: Current market prices
            
        Returns:
            Tuple of (should_exit, reason)
        """
        # Check if we have an active position
        if market_id not in self.active_positions:
            return False, ""
        
        position = self.active_positions[market_id]
        entry_price = position['entry_price']
        direction = position['direction']
        
        current_price = current_prices.get('yes', 0)
        
        # Calculate profit/loss
        if direction == 'bullish':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # bearish
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Check stop loss
        if pnl_pct <= -self.stop_loss_pct:
            return True, "stop_loss"
        
        # Check profit target
        if pnl_pct >= self.profit_target_min:
            return True, "profit_target"
        
        # Check momentum reversal
        momentum_score, metrics = self.calculate_momentum_score(market_id)
        if momentum_score < self.exit_momentum_score:
            return True, "momentum_loss"
        
        # Check price reversal
        if direction == 'bullish' and metrics['price_change_5m'] < -self.reversal_threshold:
            return True, "reversal"
        elif direction == 'bearish' and metrics['price_change_5m'] > self.reversal_threshold:
            return True, "reversal"
        
        return False, ""
    
    def enter_position(self, opportunity: MomentumOpportunity,
                       trade_size: float) -> Dict[str, Any]:
        """
        Enter a position on a momentum opportunity
        
        Args:
            opportunity: MomentumOpportunity to trade
            trade_size: Amount to invest in USD
            
        Returns:
            Position information dictionary
        """
        # Record position
        position = {
            'market_id': opportunity.market_id,
            'market_name': opportunity.market_name,
            'entry_time': datetime.now(),
            'entry_price': opportunity.current_price,
            'direction': opportunity.direction,
            'momentum_score': opportunity.momentum_score,
            'trade_size': trade_size,
            'status': 'active'
        }
        
        self.active_positions[opportunity.market_id] = position
        self.opportunities_taken += 1
        
        # Log the trade
        self.logger.log_trade(
            market=opportunity.market_name,
            yes_price=opportunity.current_price,
            no_price=1.0 - opportunity.current_price,
            profit_usd=0.0,  # Profit TBD on exit
            status=f"{self.strategy_name}_{opportunity.direction}_entered"
        )
        
        return position
    
    def exit_position(self, market_id: str, exit_price: float,
                     reason: str = "manual") -> Dict[str, Any]:
        """
        Exit a position
        
        Args:
            market_id: Market identifier
            exit_price: Exit price
            reason: Reason for exit
            
        Returns:
            Exit information dictionary
        """
        if market_id not in self.active_positions:
            return {'error': 'No active position found'}
        
        position = self.active_positions[market_id]
        
        # Calculate profit/loss
        entry_price = position['entry_price']
        direction = position['direction']
        trade_size = position['trade_size']
        
        if direction == 'bullish':
            pnl = trade_size * ((exit_price - entry_price) / entry_price)
        else:  # bearish
            pnl = trade_size * ((entry_price - exit_price) / entry_price)
        
        # Update statistics
        if pnl > 0:
            self.total_profit += pnl
        else:
            self.total_loss += abs(pnl)
        
        # Log the exit
        self.logger.log_trade(
            market=position['market_name'],
            yes_price=exit_price,
            no_price=1.0 - exit_price,
            profit_usd=pnl,
            status=f"{self.strategy_name}_exited_{reason}"
        )
        
        # Create exit record
        exit_info = {
            'market_id': market_id,
            'market_name': position['market_name'],
            'exit_time': datetime.now(),
            'exit_price': exit_price,
            'entry_price': entry_price,
            'pnl': pnl,
            'pnl_pct': (pnl / trade_size) * 100,
            'reason': reason,
            'direction': direction
        }
        
        # Remove from active positions
        del self.active_positions[market_id]
        
        return exit_info
    
    def _meets_entry_criteria(self, metrics: Dict[str, float],
                             momentum_score: float) -> bool:
        """
        Check if metrics meet entry criteria
        
        Args:
            metrics: Calculated metrics dictionary
            momentum_score: Overall momentum score
            
        Returns:
            True if meets entry criteria
        """
        # Check price change
        if abs(metrics.get('price_change_5m', 0)) < self.min_price_change_5m:
            return False
        
        # Check volume change
        if metrics.get('volume_change', 0) < self.min_volume_change:
            return False
        
        # Check momentum score
        if momentum_score < self.min_momentum_score:
            return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get strategy statistics
        
        Returns:
            Dictionary with strategy statistics
        """
        total_trades = self.opportunities_taken
        net_profit = self.total_profit - self.total_loss
        
        return {
            'strategy_name': self.strategy_name,
            'opportunities_found': self.opportunities_found,
            'opportunities_taken': self.opportunities_taken,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_profit': net_profit,
            'active_positions': len(self.active_positions),
            'win_rate': (self.total_profit / max(self.total_profit + self.total_loss, 1)) * 100
        }
    
    def reset_statistics(self) -> None:
        """Reset strategy statistics"""
        self.opportunities_found = 0
        self.opportunities_taken = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
