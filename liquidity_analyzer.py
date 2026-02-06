"""
Liquidity Analyzer Module - Deep order book analysis before trading

Ensures sufficient liquidity before executing trades by:
- Analyzing order book depth
- Estimating slippage and market impact
- Verifying liquidity requirements are met
- Preventing trades in thin/illiquid markets

Protects against failed trades and excessive slippage.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from logger import get_logger


class OrderBook:
    """Represents an order book snapshot"""
    
    def __init__(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        """
        Initialize order book
        
        Args:
            bids: List of (price, size) tuples for buy orders
            asks: List of (price, size) tuples for sell orders
        """
        self.bids = sorted(bids, key=lambda x: x[0], reverse=True)  # Highest first
        self.asks = sorted(asks, key=lambda x: x[0])  # Lowest first
        self.timestamp = datetime.now()
    
    def best_bid(self) -> Optional[float]:
        """Get best bid price"""
        return self.bids[0][0] if self.bids else None
    
    def best_ask(self) -> Optional[float]:
        """Get best ask price"""
        return self.asks[0][0] if self.asks else None
    
    def spread(self) -> float:
        """Calculate bid-ask spread"""
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        if best_bid is None or best_ask is None:
            return float('inf')
        return best_ask - best_bid
    
    def spread_percentage(self) -> float:
        """Calculate spread as percentage of mid price"""
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        if best_bid is None or best_ask is None:
            return float('inf')
        mid_price = (best_bid + best_ask) / 2
        if mid_price == 0:
            return float('inf')
        return (self.spread() / mid_price) * 100
    
    def depth_at_level(self, side: str, levels: int = 5) -> float:
        """
        Calculate total liquidity at top N levels
        
        Args:
            side: 'bid' or 'ask'
            levels: Number of levels to sum
            
        Returns:
            Total liquidity in USD
        """
        orders = self.bids if side == 'bid' else self.asks
        total = 0
        for i, (price, size) in enumerate(orders[:levels]):
            total += price * size
        return total


class LiquidityAnalyzer:
    """
    Deep order book analysis to ensure safe trade execution
    
    Prevents trading in thin markets and estimates real execution costs
    including slippage and market impact.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize liquidity analyzer
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Liquidity requirements (can be overridden by config)
        liquidity_config = config.get('liquidity_requirements', {})
        
        self.min_liquidity_multiplier = liquidity_config.get('min_liquidity_multiplier', 5.0)  # 5x position size
        self.max_spread_pct = liquidity_config.get('max_spread_pct', 0.5)  # 0.5%
        self.min_daily_volume = liquidity_config.get('min_daily_volume_usd', 1000.0)  # $1000/day
        self.order_book_levels = liquidity_config.get('order_book_levels', 5)
        
        # Track liquidity data
        self.volume_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.last_checks: Dict[str, Dict[str, Any]] = {}
        
        self.logger.log_warning(
            f"LiquidityAnalyzer initialized - "
            f"Min liquidity: {self.min_liquidity_multiplier}x position, "
            f"Max spread: {self.max_spread_pct}%, "
            f"Min daily volume: ${self.min_daily_volume}"
        )
    
    def check_depth(self, market: str, position_size: float, 
                   order_book: Optional[OrderBook] = None) -> Dict[str, Any]:
        """
        Check if market has sufficient depth for trade
        
        Args:
            market: Market identifier
            position_size: Size of intended trade in USD
            order_book: Optional OrderBook object (if None, simulates)
            
        Returns:
            Dictionary with depth analysis and pass/fail status
        """
        # If no order book provided, simulate one (for paper trading)
        if order_book is None:
            order_book = self._simulate_order_book(market)
        
        required_liquidity = position_size * self.min_liquidity_multiplier
        
        # Check bid and ask depth
        bid_depth = order_book.depth_at_level('bid', self.order_book_levels)
        ask_depth = order_book.depth_at_level('ask', self.order_book_levels)
        total_depth = bid_depth + ask_depth
        
        # Check spread
        spread_pct = order_book.spread_percentage()
        
        # Check daily volume
        daily_volume = self._get_daily_volume(market)
        
        # Determine if checks pass
        depth_check = total_depth >= required_liquidity
        spread_check = spread_pct <= self.max_spread_pct
        volume_check = daily_volume >= self.min_daily_volume
        
        all_checks_pass = depth_check and spread_check and volume_check
        
        result = {
            'market': market,
            'position_size': position_size,
            'required_liquidity': required_liquidity,
            'available_liquidity': total_depth,
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'spread_pct': spread_pct,
            'daily_volume': daily_volume,
            'checks': {
                'depth_sufficient': depth_check,
                'spread_acceptable': spread_check,
                'volume_adequate': volume_check
            },
            'passed': all_checks_pass,
            'timestamp': datetime.now()
        }
        
        # Cache result
        self.last_checks[market] = result
        
        # Log result
        if all_checks_pass:
            self.logger.log_warning(
                f"Liquidity check PASSED for {market} - "
                f"Depth: ${total_depth:.2f}, Spread: {spread_pct:.2f}%"
            )
        else:
            failed_checks = [k for k, v in result['checks'].items() if not v]
            self.logger.log_warning(
                f"Liquidity check FAILED for {market} - "
                f"Failed: {', '.join(failed_checks)}"
            )
        
        return result
    
    def estimate_slippage(self, order_size: float, book_depth: float) -> float:
        """
        Estimate slippage for an order
        
        Args:
            order_size: Size of order in USD
            book_depth: Available liquidity in order book
            
        Returns:
            Estimated slippage as percentage
        """
        if book_depth == 0:
            return 100.0  # Maximum slippage if no liquidity
        
        # Simple slippage model: slippage increases with order size relative to depth
        depth_ratio = order_size / book_depth
        
        # Exponential slippage model
        if depth_ratio < 0.1:
            # Small orders: minimal slippage
            slippage_pct = depth_ratio * 0.5
        elif depth_ratio < 0.5:
            # Medium orders: moderate slippage
            slippage_pct = 0.05 + (depth_ratio - 0.1) * 2.0
        else:
            # Large orders: significant slippage
            slippage_pct = 0.85 + (depth_ratio - 0.5) * 5.0
        
        return min(slippage_pct, 100.0)  # Cap at 100%
    
    def calculate_market_impact(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate expected market impact of a trade
        
        Args:
            trade: Trade details with 'market', 'size', 'order_book'
            
        Returns:
            Dictionary with market impact analysis
        """
        market = trade['market']
        size = trade['size']
        order_book = trade.get('order_book')
        
        if order_book is None:
            order_book = self._simulate_order_book(market)
        
        # Get liquidity depth
        bid_depth = order_book.depth_at_level('bid', self.order_book_levels)
        ask_depth = order_book.depth_at_level('ask', self.order_book_levels)
        
        # Estimate slippage for both sides
        buy_slippage = self.estimate_slippage(size / 2, ask_depth)
        sell_slippage = self.estimate_slippage(size / 2, bid_depth)
        avg_slippage = (buy_slippage + sell_slippage) / 2
        
        # Calculate impact cost
        impact_cost = size * (avg_slippage / 100)
        
        return {
            'market': market,
            'trade_size': size,
            'buy_slippage_pct': buy_slippage,
            'sell_slippage_pct': sell_slippage,
            'avg_slippage_pct': avg_slippage,
            'estimated_impact_cost': impact_cost,
            'impact_severity': self._classify_impact(avg_slippage)
        }
    
    def verify_before_execution(self, opportunity: Any) -> Tuple[bool, str]:
        """
        Final liquidity verification right before trade execution
        
        Args:
            opportunity: Arbitrage opportunity to verify
            
        Returns:
            Tuple of (is_safe, reason)
        """
        market = opportunity.market_name if hasattr(opportunity, 'market_name') else 'unknown'
        
        # Get position size from config
        position_size = self.config.get('max_trade_size', 10)
        
        # Perform depth check
        depth_check = self.check_depth(market, position_size)
        
        if not depth_check['passed']:
            failed_checks = [k for k, v in depth_check['checks'].items() if not v]
            reason = f"Liquidity insufficient: {', '.join(failed_checks)}"
            return False, reason
        
        # Check if opportunity is still fresh
        if hasattr(opportunity, 'detected_at'):
            age = (datetime.now() - opportunity.detected_at).total_seconds()
            if age > 5.0:  # Opportunity older than 5 seconds
                return False, "Opportunity too old - may be stale"
        
        return True, "All liquidity checks passed"
    
    def _simulate_order_book(self, market: str) -> OrderBook:
        """
        Simulate an order book for paper trading
        
        Args:
            market: Market identifier
            
        Returns:
            Simulated OrderBook object
        """
        # Generate realistic-looking order book
        # In production, this would fetch real order book data
        
        import random
        
        # Simulate bid orders (descending prices)
        bids = []
        base_bid = 0.50
        for i in range(10):
            price = base_bid - (i * 0.01)
            size = random.uniform(100, 500) * (1 + i * 0.1)  # Deeper levels have more size
            bids.append((price, size))
        
        # Simulate ask orders (ascending prices)
        asks = []
        base_ask = 0.51
        for i in range(10):
            price = base_ask + (i * 0.01)
            size = random.uniform(100, 500) * (1 + i * 0.1)
            asks.append((price, size))
        
        return OrderBook(bids, asks)
    
    def _get_daily_volume(self, market: str) -> float:
        """
        Get 24-hour trading volume for market
        
        Args:
            market: Market identifier
            
        Returns:
            Volume in USD
        """
        # Clean old volume data
        self._clean_old_volume_data(market)
        
        # Get volume history
        if market not in self.volume_history:
            # For paper trading, simulate volume
            import random
            return random.uniform(500, 5000)
        
        # Sum volume from last 24 hours
        cutoff_time = datetime.now() - timedelta(days=1)
        recent_volume = [
            vol for timestamp, vol in self.volume_history[market]
            if timestamp > cutoff_time
        ]
        
        return sum(recent_volume) if recent_volume else 0
    
    def record_volume(self, market: str, volume: float) -> None:
        """
        Record trading volume for a market
        
        Args:
            market: Market identifier
            volume: Trading volume in USD
        """
        if market not in self.volume_history:
            self.volume_history[market] = []
        
        self.volume_history[market].append((datetime.now(), volume))
    
    def _clean_old_volume_data(self, market: str) -> None:
        """Remove volume data older than 24 hours"""
        if market not in self.volume_history:
            return
        
        cutoff_time = datetime.now() - timedelta(days=1)
        self.volume_history[market] = [
            (timestamp, vol) for timestamp, vol in self.volume_history[market]
            if timestamp > cutoff_time
        ]
    
    def _classify_impact(self, slippage_pct: float) -> str:
        """
        Classify market impact severity
        
        Args:
            slippage_pct: Estimated slippage percentage
            
        Returns:
            Impact severity: 'low', 'medium', 'high', 'extreme'
        """
        if slippage_pct < 0.1:
            return 'low'
        elif slippage_pct < 0.5:
            return 'medium'
        elif slippage_pct < 2.0:
            return 'high'
        else:
            return 'extreme'
    
    def get_liquidity_summary(self) -> Dict[str, Any]:
        """
        Get summary of recent liquidity checks
        
        Returns:
            Dictionary with liquidity statistics
        """
        if not self.last_checks:
            return {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'pass_rate': 0
            }
        
        total = len(self.last_checks)
        passed = sum(1 for check in self.last_checks.values() if check['passed'])
        failed = total - passed
        
        return {
            'total_checks': total,
            'passed_checks': passed,
            'failed_checks': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'markets_checked': list(self.last_checks.keys())
        }
