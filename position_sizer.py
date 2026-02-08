"""
Position Sizer Module - Dynamic position sizing based on risk factors

Calculates optimal position size for each trade based on:
- Profit margin quality (higher = larger size)
- Recent win rate (hot streak = larger, cold = smaller)
- Market liquidity (thin markets = smaller size)
- Market volatility (high vol = smaller size)

Base: 5% of bankroll
Hard limits: Max 10%, Min $1 per trade
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from logger import get_logger
from detector import ArbitrageOpportunity


class RiskAdjustedPositionSizer:
    """
    Dynamically calculates position size based on multiple risk factors

    Uses a base allocation of 5% of bankroll, then adjusts based on:
    - Profit margin quality
    - Recent win rate (hot/cold streak detection)
    - Market liquidity
    - Volatility
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize position sizer

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()

        # Base allocation (5% of bankroll)
        self.base_allocation_pct = config.get("position_sizing", {}).get(
            "base_allocation_pct", 0.05
        )

        # Hard limits
        self.max_allocation_pct = config.get("position_sizing", {}).get(
            "max_allocation_pct", 0.10
        )
        self.min_position_size = config.get("position_sizing", {}).get(
            "min_position_size", 1.0
        )

        # Multipliers for different factors
        multipliers = config.get("position_sizing", {}).get("multipliers", {})
        self.profit_margin_multipliers = multipliers.get(
            "profit_margin",
            {
                "excellent": 1.5,  # >5% margin
                "good": 1.2,  # 3-5% margin
                "normal": 1.0,  # 2-3% margin
                "poor": 0.7,  # <2% margin
            },
        )

        self.win_rate_multipliers = multipliers.get(
            "win_rate",
            {
                "hot_streak": 1.3,  # >70% win rate
                "normal": 1.0,  # 50-70% win rate
                "cold_streak": 0.6,  # <50% win rate
            },
        )

        self.liquidity_multipliers = multipliers.get(
            "liquidity",
            {
                "high": 1.0,  # High volume markets
                "medium": 0.85,  # Medium volume
                "low": 0.6,  # Low volume (thin markets)
            },
        )

        self.volatility_multipliers = multipliers.get(
            "volatility",
            {
                "low": 1.1,  # Stable prices
                "normal": 1.0,  # Normal volatility
                "high": 0.7,  # High volatility
            },
        )

        self.logger.log_warning(
            f"Position Sizer initialized - Base: {self.base_allocation_pct*100:.1f}%, "
            f"Max: {self.max_allocation_pct*100:.1f}%, Min: ${self.min_position_size:.2f}"
        )

    def calculate_position_size(
        self,
        opportunity: ArbitrageOpportunity,
        bankroll: float,
        stats: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate position size for a trade opportunity

        Args:
            opportunity: Arbitrage opportunity to size
            bankroll: Current available bankroll
            stats: Trading statistics (win rate, recent performance, etc.)

        Returns:
            Dictionary with position_size and sizing_details for logging
        """
        # Start with base allocation
        base_size = bankroll * self.base_allocation_pct

        # Initialize multipliers
        profit_margin_mult = 1.0
        win_rate_mult = 1.0
        liquidity_mult = 1.0
        volatility_mult = 1.0

        # Adjust for profit margin quality
        profit_margin_mult, margin_reasoning = self._assess_profit_margin(opportunity)

        # Adjust for win rate (hot/cold streak)
        if stats:
            win_rate_mult, win_rate_reasoning = self._assess_win_rate(stats)
            liquidity_mult, liquidity_reasoning = self._assess_liquidity(
                opportunity, stats
            )
            volatility_mult, volatility_reasoning = self._assess_volatility(
                opportunity, stats
            )
        else:
            win_rate_reasoning = "No stats available - using normal multiplier"
            liquidity_reasoning = "No liquidity data - using normal multiplier"
            volatility_reasoning = "No volatility data - using normal multiplier"

        # Calculate adjusted size
        total_multiplier = (
            profit_margin_mult * win_rate_mult * liquidity_mult * volatility_mult
        )

        adjusted_size = base_size * total_multiplier

        # Apply hard limits
        max_size = bankroll * self.max_allocation_pct
        final_size = max(self.min_position_size, min(adjusted_size, max_size))

        # Determine which limit was hit (if any)
        limit_applied = None
        if adjusted_size < self.min_position_size:
            limit_applied = f"min (${self.min_position_size:.2f})"
        elif adjusted_size > max_size:
            limit_applied = f"max ({self.max_allocation_pct*100:.1f}% of bankroll)"

        # Build detailed reasoning
        sizing_details = {
            "base_size": base_size,
            "bankroll": bankroll,
            "multipliers": {
                "profit_margin": profit_margin_mult,
                "win_rate": win_rate_mult,
                "liquidity": liquidity_mult,
                "volatility": volatility_mult,
                "total": total_multiplier,
            },
            "adjusted_size": adjusted_size,
            "final_size": final_size,
            "limit_applied": limit_applied,
            "reasoning": {
                "profit_margin": margin_reasoning,
                "win_rate": win_rate_reasoning,
                "liquidity": liquidity_reasoning,
                "volatility": volatility_reasoning,
            },
        }

        # Log the sizing decision
        self._log_sizing_decision(opportunity, sizing_details)

        return {"position_size": final_size, "details": sizing_details}

    def _assess_profit_margin(self, opportunity: ArbitrageOpportunity) -> tuple:
        """
        Assess profit margin quality and return multiplier

        Args:
            opportunity: Arbitrage opportunity

        Returns:
            Tuple of (multiplier, reasoning string)
        """
        margin = opportunity.profit_margin

        if margin >= 5.0:
            return (
                self.profit_margin_multipliers["excellent"],
                f"Excellent margin ({margin:.2f}%) - sizing up {self.profit_margin_multipliers['excellent']:.1f}x",
            )
        elif margin >= 3.0:
            return (
                self.profit_margin_multipliers["good"],
                f"Good margin ({margin:.2f}%) - sizing up {self.profit_margin_multipliers['good']:.1f}x",
            )
        elif margin >= 2.0:
            return (
                self.profit_margin_multipliers["normal"],
                f"Normal margin ({margin:.2f}%) - normal sizing",
            )
        else:
            return (
                self.profit_margin_multipliers["poor"],
                f"Poor margin ({margin:.2f}%) - sizing down {self.profit_margin_multipliers['poor']:.1f}x",
            )

    def _assess_win_rate(self, stats: Dict[str, Any]) -> tuple:
        """
        Assess recent win rate and detect hot/cold streaks

        Args:
            stats: Trading statistics

        Returns:
            Tuple of (multiplier, reasoning string)
        """
        win_rate = stats.get("win_rate", 0.5)  # Default 50%
        total_trades = stats.get("total_trades", 0)

        # Need minimum sample size for reliable assessment
        if total_trades < 10:
            return (
                self.win_rate_multipliers["normal"],
                f"Limited history ({total_trades} trades) - normal sizing",
            )

        if win_rate >= 0.70:
            return (
                self.win_rate_multipliers["hot_streak"],
                f"Hot streak! ({win_rate*100:.1f}% win rate) - sizing up {self.win_rate_multipliers['hot_streak']:.1f}x",
            )
        elif win_rate >= 0.50:
            return (
                self.win_rate_multipliers["normal"],
                f"Normal win rate ({win_rate*100:.1f}%) - normal sizing",
            )
        else:
            return (
                self.win_rate_multipliers["cold_streak"],
                f"Cold streak ({win_rate*100:.1f}% win rate) - sizing down {self.win_rate_multipliers['cold_streak']:.1f}x",
            )

    def _assess_liquidity(
        self, opportunity: ArbitrageOpportunity, stats: Dict[str, Any]
    ) -> tuple:
        """
        Assess market liquidity (thin markets require smaller positions)

        Args:
            opportunity: Arbitrage opportunity
            stats: Trading statistics

        Returns:
            Tuple of (multiplier, reasoning string)
        """
        # Check if we have liquidity data in stats
        market_liquidity = stats.get("market_liquidity", {}).get(
            opportunity.market_id, "medium"
        )

        if market_liquidity == "high":
            return (
                self.liquidity_multipliers["high"],
                "High liquidity market - normal sizing",
            )
        elif market_liquidity == "medium":
            return (
                self.liquidity_multipliers["medium"],
                f"Medium liquidity - sizing down {self.liquidity_multipliers['medium']:.2f}x",
            )
        else:  # low
            return (
                self.liquidity_multipliers["low"],
                f"Low liquidity (thin market) - sizing down {self.liquidity_multipliers['low']:.2f}x",
            )

    def _assess_volatility(
        self, opportunity: ArbitrageOpportunity, stats: Dict[str, Any]
    ) -> tuple:
        """
        Assess market volatility (high vol = smaller positions)

        Args:
            opportunity: Arbitrage opportunity
            stats: Trading statistics

        Returns:
            Tuple of (multiplier, reasoning string)
        """
        # Check if we have volatility data in stats
        market_volatility = stats.get("market_volatility", {}).get(
            opportunity.market_id, "normal"
        )

        if market_volatility == "low":
            return (
                self.volatility_multipliers["low"],
                f"Low volatility - sizing up {self.volatility_multipliers['low']:.1f}x",
            )
        elif market_volatility == "normal":
            return (
                self.volatility_multipliers["normal"],
                "Normal volatility - normal sizing",
            )
        else:  # high
            return (
                self.volatility_multipliers["high"],
                f"High volatility - sizing down {self.volatility_multipliers['high']:.1f}x",
            )

    def _log_sizing_decision(
        self, opportunity: ArbitrageOpportunity, details: Dict[str, Any]
    ) -> None:
        """
        Log the position sizing decision with full reasoning

        Args:
            opportunity: Arbitrage opportunity
            details: Sizing details dictionary
        """
        # Build a concise log message
        mult = details["multipliers"]
        reasoning = details["reasoning"]

        log_msg = (
            f"Position Sizing for {opportunity.market_name}: "
            f"${details['final_size']:.2f} "
            f"(Base: ${details['base_size']:.2f} * "
            f"Margin: {mult['profit_margin']:.2f}x * "
            f"WinRate: {mult['win_rate']:.2f}x * "
            f"Liquidity: {mult['liquidity']:.2f}x * "
            f"Volatility: {mult['volatility']:.2f}x) "
        )

        if details["limit_applied"]:
            log_msg += f"[Limited by {details['limit_applied']}]"

        self.logger.log_warning(log_msg)

        # Log detailed reasoning
        for factor, reason in reasoning.items():
            self.logger.log_warning(f"  {factor.title()}: {reason}")

    def get_sizing_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about position sizing

        Returns:
            Dictionary with sizing statistics
        """
        return {
            "base_allocation_pct": self.base_allocation_pct * 100,
            "max_allocation_pct": self.max_allocation_pct * 100,
            "min_position_size": self.min_position_size,
            "multipliers": {
                "profit_margin": self.profit_margin_multipliers,
                "win_rate": self.win_rate_multipliers,
                "liquidity": self.liquidity_multipliers,
                "volatility": self.volatility_multipliers,
            },
        }
