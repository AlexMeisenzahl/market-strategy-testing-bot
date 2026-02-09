"""
BTC Arbitrage Strategy Module

Implements Bitcoin volatility arbitrage on Polymarket's 15-minute BTC UP/DOWN markets.
Captures risk-free profit when UP_price + DOWN_price < $1.00.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from logger import get_logger
import time


@dataclass
class ArbitrageOpportunity:
    """Represents a BTC arbitrage opportunity"""
    
    up_market_id: str
    down_market_id: str
    up_market_name: str
    down_market_name: str
    up_price: float
    down_price: float
    total_cost: float  # up_price + down_price
    profit: float  # 1.00 - total_cost
    profit_margin: float  # profit / total_cost
    expiry_time: datetime
    seconds_until_expiry: int
    estimated_fees: float
    estimated_slippage: float
    net_profit: float  # profit - fees - slippage
    confidence: float  # 0.0 to 1.0
    reasoning: str


class BTCArbitrageStrategy:
    """
    Bitcoin Volatility Arbitrage Strategy
    
    Monitors 15-minute BTC UP/DOWN markets on Polymarket and captures
    arbitrage opportunities when the sum of prices is less than $1.00.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize BTC arbitrage strategy
        
        Args:
            config: Configuration dictionary with BTC arbitrage settings
        """
        self.config = config
        self.logger = get_logger()
        
        # Extract configuration
        self.min_profit_margin = config.get('min_profit_margin', 0.02)
        self.max_position_size = config.get('max_position_size', 500)
        self.expiry_minutes = config.get('expiry_minutes', 15)
        self.slippage_tolerance = config.get('slippage_tolerance', 0.005)
        self.max_gas_price = config.get('max_gas_price', 50)
        
        # Trading fee estimate (Polymarket charges ~2% on profits)
        self.trading_fee_rate = 0.02
        
        # Track active positions
        self.active_positions: Dict[str, Dict] = {}
        
        # Track market pairs
        self.market_pairs: Dict[str, Tuple[str, str]] = {}  # expiry_time -> (up_id, down_id)
        
        self.logger.log_info(
            f"BTC Arbitrage Strategy initialized with min profit margin: {self.min_profit_margin:.2%}"
        )
    
    def find_opportunities(self, markets: List[Dict]) -> List[ArbitrageOpportunity]:
        """
        Find BTC arbitrage opportunities
        
        Args:
            markets: List of available markets
            
        Returns:
            List of identified arbitrage opportunities
        """
        opportunities = []
        
        # First, identify and pair BTC UP/DOWN markets
        btc_markets = self._identify_btc_markets(markets)
        market_pairs = self._pair_markets(btc_markets)
        
        # Analyze each pair for arbitrage
        for up_market, down_market in market_pairs:
            try:
                opportunity = self.analyze_pair(up_market, down_market)
                
                if opportunity and opportunity.profit_margin >= self.min_profit_margin:
                    opportunities.append(opportunity)
                    self.logger.log_info(
                        f"BTC Arbitrage opportunity: {opportunity.profit_margin:.2%} profit "
                        f"({opportunity.net_profit:.2f} USD net)"
                    )
            except Exception as e:
                self.logger.log_error(f"Error analyzing BTC market pair: {e}")
                continue
        
        return opportunities
    
    def _identify_btc_markets(self, markets: List[Dict]) -> List[Dict]:
        """
        Identify BTC UP/DOWN markets
        
        Args:
            markets: List of all markets
            
        Returns:
            List of BTC-related markets
        """
        btc_markets = []
        
        for market in markets:
            question = market.get('question', '').lower()
            
            # Look for BTC/Bitcoin markets with UP/DOWN or directional indicators
            if ('btc' in question or 'bitcoin' in question):
                # Check for UP/DOWN or directional keywords
                if any(keyword in question for keyword in ['up', 'down', 'higher', 'lower', 'above', 'below']):
                    # Check for 15-minute or short-term expiry
                    if any(keyword in question for keyword in ['15 min', '15-min', '15min', 'fifteen minute']):
                        btc_markets.append(market)
        
        return btc_markets
    
    def _pair_markets(self, btc_markets: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """
        Pair UP and DOWN markets for the same expiry time
        
        Args:
            btc_markets: List of BTC markets
            
        Returns:
            List of (up_market, down_market) tuples
        """
        pairs = []
        
        # Group markets by expiry time
        expiry_groups: Dict[str, List[Dict]] = {}
        
        for market in btc_markets:
            # Extract expiry time from market
            expiry = self._extract_expiry_time(market)
            
            if expiry:
                expiry_key = expiry.isoformat()
                if expiry_key not in expiry_groups:
                    expiry_groups[expiry_key] = []
                expiry_groups[expiry_key].append(market)
        
        # Pair UP and DOWN markets for each expiry
        for expiry_key, markets in expiry_groups.items():
            up_markets = [m for m in markets if self._is_up_market(m)]
            down_markets = [m for m in markets if self._is_down_market(m)]
            
            # Create pairs (assuming 1:1 pairing)
            for up_market in up_markets:
                for down_market in down_markets:
                    # Verify they're for the same underlying event
                    if self._markets_match(up_market, down_market):
                        pairs.append((up_market, down_market))
                        break  # Move to next up_market
        
        return pairs
    
    def _extract_expiry_time(self, market: Dict) -> Optional[datetime]:
        """
        Extract expiry time from market data
        
        Args:
            market: Market data
            
        Returns:
            Expiry datetime or None
        """
        # Try to get from market metadata
        end_date = market.get('end_date') or market.get('endDate')
        
        if end_date:
            try:
                if isinstance(end_date, str):
                    return datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                elif isinstance(end_date, (int, float)):
                    return datetime.fromtimestamp(end_date)
            except:
                pass
        
        # If not available, estimate based on 15-minute intervals
        # Round current time up to next 15-minute mark
        now = datetime.now()
        minutes = now.minute
        next_interval = ((minutes // 15) + 1) * 15
        
        if next_interval >= 60:
            expiry = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            expiry = now.replace(minute=next_interval, second=0, microsecond=0)
        
        return expiry
    
    def _is_up_market(self, market: Dict) -> bool:
        """Check if market is an UP market"""
        question = market.get('question', '').lower()
        return 'up' in question or 'higher' in question or 'above' in question
    
    def _is_down_market(self, market: Dict) -> bool:
        """Check if market is a DOWN market"""
        question = market.get('question', '').lower()
        return 'down' in question or 'lower' in question or 'below' in question
    
    def _markets_match(self, up_market: Dict, down_market: Dict) -> bool:
        """
        Check if UP and DOWN markets are for the same event
        
        Args:
            up_market: UP market data
            down_market: DOWN market data
            
        Returns:
            True if markets match
        """
        # Simple heuristic: check if they have similar market IDs or parent market
        up_parent = up_market.get('parent_market_id') or up_market.get('groupItemId')
        down_parent = down_market.get('parent_market_id') or down_market.get('groupItemId')
        
        if up_parent and down_parent:
            return up_parent == down_parent
        
        # Fallback: check if questions are similar (excluding UP/DOWN)
        up_q = up_market.get('question', '').lower()
        down_q = down_market.get('question', '').lower()
        
        # Remove directional words
        for word in ['up', 'down', 'higher', 'lower', 'above', 'below']:
            up_q = up_q.replace(word, '')
            down_q = down_q.replace(word, '')
        
        # Check similarity (simple approach)
        up_words = set(up_q.split())
        down_words = set(down_q.split())
        
        if not up_words or not down_words:
            return False
        
        similarity = len(up_words & down_words) / len(up_words | down_words)
        return similarity > 0.7
    
    def analyze_pair(self, up_market: Dict, down_market: Dict) -> Optional[ArbitrageOpportunity]:
        """
        Analyze a UP/DOWN market pair for arbitrage opportunity
        
        Args:
            up_market: UP market data
            down_market: DOWN market data
            
        Returns:
            ArbitrageOpportunity or None if no opportunity
        """
        # Get prices
        up_price = up_market.get('yes_price', up_market.get('price', 0.5))
        down_price = down_market.get('yes_price', down_market.get('price', 0.5))
        
        # Calculate total cost and profit
        total_cost = up_price + down_price
        profit = 1.0 - total_cost
        
        # Must have profit to be an arbitrage
        if profit <= 0:
            return None
        
        profit_margin = profit / total_cost if total_cost > 0 else 0
        
        # Extract expiry time
        expiry_time = self._extract_expiry_time(up_market)
        seconds_until_expiry = (expiry_time - datetime.now()).total_seconds() if expiry_time else 0
        
        # Estimate costs
        estimated_fees = total_cost * self.trading_fee_rate
        estimated_slippage = total_cost * self.slippage_tolerance
        
        # Calculate net profit
        net_profit = profit - estimated_fees - estimated_slippage
        
        # Confidence calculation
        confidence = self._calculate_confidence(
            profit_margin,
            seconds_until_expiry,
            up_price,
            down_price
        )
        
        # Generate reasoning
        reasoning = (
            f"UP price: ${up_price:.3f}, DOWN price: ${down_price:.3f}, "
            f"Total: ${total_cost:.3f}, Gross profit: ${profit:.3f}, "
            f"Net profit: ${net_profit:.3f} after fees and slippage"
        )
        
        return ArbitrageOpportunity(
            up_market_id=up_market.get('id', ''),
            down_market_id=down_market.get('id', ''),
            up_market_name=up_market.get('question', ''),
            down_market_name=down_market.get('question', ''),
            up_price=up_price,
            down_price=down_price,
            total_cost=total_cost,
            profit=profit,
            profit_margin=profit_margin,
            expiry_time=expiry_time or datetime.now(),
            seconds_until_expiry=int(seconds_until_expiry),
            estimated_fees=estimated_fees,
            estimated_slippage=estimated_slippage,
            net_profit=net_profit,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _calculate_confidence(
        self,
        profit_margin: float,
        seconds_until_expiry: float,
        up_price: float,
        down_price: float
    ) -> float:
        """
        Calculate confidence in arbitrage opportunity
        
        Args:
            profit_margin: Profit margin
            seconds_until_expiry: Time until market expiry
            up_price: UP market price
            down_price: DOWN market price
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5
        
        # Higher profit margin = higher confidence
        if profit_margin > 0.05:
            confidence += 0.3
        elif profit_margin > 0.03:
            confidence += 0.2
        else:
            confidence += 0.1
        
        # More time until expiry = lower risk of price changes
        if seconds_until_expiry > 600:  # > 10 minutes
            confidence += 0.1
        elif seconds_until_expiry > 300:  # > 5 minutes
            confidence += 0.05
        
        # Balanced prices (closer to 0.5 each) = more liquid, easier to execute
        avg_distance_from_half = (abs(up_price - 0.5) + abs(down_price - 0.5)) / 2
        if avg_distance_from_half < 0.1:
            confidence += 0.1
        elif avg_distance_from_half < 0.2:
            confidence += 0.05
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> bool:
        """
        Execute arbitrage trade (buy both UP and DOWN)
        
        Args:
            opportunity: Arbitrage opportunity to execute
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.log_info(
            f"Executing BTC arbitrage: {opportunity.up_market_name} + {opportunity.down_market_name}"
        )
        
        try:
            # In paper trading mode, we just log the trade
            # In live mode, this would execute actual trades
            
            # Record position
            position_id = f"{opportunity.up_market_id}_{opportunity.down_market_id}"
            
            self.active_positions[position_id] = {
                'opportunity': opportunity,
                'entry_time': datetime.now(),
                'status': 'active',
                'up_filled': True,  # Simulated
                'down_filled': True,  # Simulated
            }
            
            self.logger.log_info(
                f"Arbitrage executed successfully. Net profit: ${opportunity.net_profit:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"Failed to execute arbitrage: {e}")
            
            # Rollback logic would go here in live mode
            # If only one side filled, immediately close it
            
            return False
    
    def monitor_expiry(self, position: Dict) -> None:
        """
        Monitor position and handle expiry
        
        Args:
            position: Position data
        """
        opportunity = position.get('opportunity')
        if not opportunity:
            return
        
        # Calculate time until expiry
        time_until_expiry = (opportunity.expiry_time - datetime.now()).total_seconds()
        
        if time_until_expiry <= 0:
            # Market has expired, settle position
            self._settle_position(position)
        elif time_until_expiry <= 60:
            # Less than 1 minute to expiry, prepare for settlement
            self.logger.log_info(
                f"Position expiring in {time_until_expiry:.0f} seconds: "
                f"{opportunity.up_market_name}"
            )
    
    def _settle_position(self, position: Dict) -> None:
        """
        Settle an expired position
        
        Args:
            position: Position data
        """
        opportunity = position.get('opportunity')
        position_id = f"{opportunity.up_market_id}_{opportunity.down_market_id}"
        
        # One of UP or DOWN will be YES, the other NO
        # Since we bought both, we're guaranteed to profit
        
        self.logger.log_info(
            f"Position settled: {opportunity.up_market_name}. "
            f"Realized profit: ${opportunity.net_profit:.2f}"
        )
        
        # Mark as settled
        if position_id in self.active_positions:
            self.active_positions[position_id]['status'] = 'settled'
            self.active_positions[position_id]['settlement_time'] = datetime.now()
    
    def get_active_positions(self) -> List[Dict]:
        """
        Get all active positions
        
        Returns:
            List of active positions
        """
        return [
            pos for pos in self.active_positions.values()
            if pos.get('status') == 'active'
        ]
    
    def cleanup_old_positions(self, max_age_hours: int = 24) -> None:
        """
        Remove old settled positions from tracking
        
        Args:
            max_age_hours: Maximum age in hours to keep positions
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        positions_to_remove = []
        for position_id, position in self.active_positions.items():
            if position.get('status') == 'settled':
                settlement_time = position.get('settlement_time')
                if settlement_time and settlement_time < cutoff_time:
                    positions_to_remove.append(position_id)
        
        for position_id in positions_to_remove:
            del self.active_positions[position_id]
        
        if positions_to_remove:
            self.logger.log_info(f"Cleaned up {len(positions_to_remove)} old positions")
    
    def get_name(self) -> str:
        """Get strategy name"""
        return "btc_arbitrage"
    
    def get_type(self) -> str:
        """Get strategy type"""
        return "arbitrage"
