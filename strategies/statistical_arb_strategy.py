"""
Statistical Arbitrage Strategy Module

Correlation-based trading strategy that identifies pairs of markets that
historically move together, then trades when they diverge, betting on
convergence back to their historical relationship.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
import math
from logger import get_logger
from engine import TradeSignal


class CorrelationTracker:
    """Track price correlation between two markets"""

    def __init__(self, market_id_1: str, market_id_2: str, window_size: int = 100):
        """
        Initialize correlation tracker

        Args:
            market_id_1: First market identifier
            market_id_2: Second market identifier
            window_size: Number of data points for correlation calculation
        """
        self.market_id_1 = market_id_1
        self.market_id_2 = market_id_2
        self.window_size = window_size

        # Store price pairs [(timestamp, price1, price2), ...]
        self.price_pairs: deque = deque(maxlen=window_size)

    def add_price_pair(self, price1: float, price2: float) -> None:
        """Add a new price pair observation"""
        self.price_pairs.append((datetime.now(), price1, price2))

    def calculate_correlation(self) -> float:
        """
        Calculate Pearson correlation coefficient

        Returns:
            Correlation coefficient between -1 and 1
        """
        if len(self.price_pairs) < 10:
            return 0.0

        prices1 = [p[1] for p in self.price_pairs]
        prices2 = [p[2] for p in self.price_pairs]

        n = len(prices1)

        # Calculate means
        mean1 = sum(prices1) / n
        mean2 = sum(prices2) / n

        # Calculate correlation coefficient
        numerator = sum((prices1[i] - mean1) * (prices2[i] - mean2) for i in range(n))

        sum_sq1 = sum((p - mean1) ** 2 for p in prices1)
        sum_sq2 = sum((p - mean2) ** 2 for p in prices2)

        denominator = math.sqrt(sum_sq1 * sum_sq2)

        if denominator == 0:
            return 0.0

        correlation = numerator / denominator
        return max(-1.0, min(1.0, correlation))  # Clamp to [-1, 1]

    def calculate_z_score(self, current_price1: float, current_price2: float) -> float:
        """
        Calculate z-score of current price divergence

        Args:
            current_price1: Current price of market 1
            current_price2: Current price of market 2

        Returns:
            Z-score indicating how many standard deviations from mean
        """
        if len(self.price_pairs) < 10:
            return 0.0

        # Calculate spread (difference) for all historical pairs
        spreads = [p[1] - p[2] for p in self.price_pairs]

        # Calculate mean and std dev of spread
        mean_spread = sum(spreads) / len(spreads)
        variance = sum((s - mean_spread) ** 2 for s in spreads) / len(spreads)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return 0.0

        # Calculate current spread
        current_spread = current_price1 - current_price2

        # Calculate z-score
        z_score = (current_spread - mean_spread) / std_dev
        return z_score


class StatisticalArbOpportunity:
    """Represents a statistical arbitrage opportunity"""

    def __init__(
        self,
        market_id_1: str,
        market_name_1: str,
        market_id_2: str,
        market_name_2: str,
        correlation: float,
        divergence_pct: float,
        z_score: float,
        direction: str,
        price_1: float,
        price_2: float,
    ):
        """
        Initialize statistical arbitrage opportunity

        Args:
            market_id_1: First market identifier
            market_name_1: First market name
            market_id_2: Second market identifier
            market_name_2: Second market name
            correlation: Historical correlation coefficient
            divergence_pct: Current divergence percentage
            z_score: Z-score of divergence
            direction: 'market1_high' or 'market2_high'
            price_1: Current price of market 1
            price_2: Current price of market 2
        """
        self.market_id_1 = market_id_1
        self.market_name_1 = market_name_1
        self.market_id_2 = market_id_2
        self.market_name_2 = market_name_2
        self.correlation = correlation
        self.divergence_pct = divergence_pct
        self.z_score = z_score
        self.direction = direction
        self.price_1 = price_1
        self.price_2 = price_2
        self.detected_at = datetime.now()
        self.opportunity_type = "statistical_arb"

    def get_pair_id(self) -> str:
        """Get unique identifier for this pair"""
        # Sort IDs to ensure consistent pair identification
        ids = sorted([self.market_id_1, self.market_id_2])
        return f"{ids[0]}_{ids[1]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "market_id_1": self.market_id_1,
            "market_name_1": self.market_name_1,
            "market_id_2": self.market_id_2,
            "market_name_2": self.market_name_2,
            "correlation": self.correlation,
            "divergence_pct": self.divergence_pct,
            "z_score": self.z_score,
            "direction": self.direction,
            "price_1": self.price_1,
            "price_2": self.price_2,
            "opportunity_type": self.opportunity_type,
            "strategy": "crypto_statistical_arb",
            "arbitrage_type": "N/A",
            "detected_at": self.detected_at.isoformat(),
        }


class StatisticalArbStrategy:
    """
    Statistical arbitrage strategy based on correlation

    Identifies pairs of markets that historically move together, then
    trades when they diverge significantly, betting on convergence.

    Strategy Logic:
    1. Build correlation matrix of all markets
    2. Find highly correlated pairs (>0.7 correlation)
    3. Detect when pairs diverge significantly (>15%)
    4. Enter positions betting on convergence
    5. Exit when convergence occurs or stop loss hit

    Entry Criteria:
    - Historical correlation >0.7
    - Current divergence >15%
    - Z-score >2.0 (statistical significance)

    Exit Criteria:
    - Convergence (z-score < 0.5)
    - Profit target (+20%)
    - Stop loss (-20%)
    - Correlation breakdown (< 0.5)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize statistical arbitrage strategy

        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.logger = get_logger()
        self.strategy_name = "crypto_statistical_arb"

        # Strategy parameters
        self.min_correlation = config.get("stat_arb_min_correlation", 0.7)
        self.min_divergence_pct = config.get("stat_arb_min_divergence", 15.0)  # 15%
        self.min_z_score = config.get("stat_arb_min_z_score", 2.0)
        self.exit_z_score = config.get("stat_arb_exit_z_score", 0.5)
        self.profit_target_pct = config.get("stat_arb_profit_target", 20.0)  # 20%
        self.stop_loss_pct = config.get("stat_arb_stop_loss", 20.0)  # 20%
        self.correlation_breakdown_threshold = config.get(
            "stat_arb_correlation_breakdown", 0.5
        )

        # Correlation tracking (pair_id -> CorrelationTracker)
        self.correlation_trackers: Dict[str, CorrelationTracker] = {}

        # Current prices cache (market_id -> price)
        self.current_prices: Dict[str, float] = {}

        # DEPRECATED: strategies do not own execution state.
        # Kept only for backward compatibility / analytics.
        # Statistics tracking
        self.opportunities_found = 0
        self.opportunities_taken = 0
        self.total_profit = 0.0
        self.total_loss = 0.0

        # Active positions (pair_id -> position info)
        self.active_positions: Dict[str, Dict[str, Any]] = {}

    def update_market_prices(
        self, markets: List[Dict[str, Any]], prices_dict: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Update price tracking for all markets

        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data
        """
        # Update current prices cache
        for market in markets:
            market_id = market.get("id", market.get("market_id", "unknown"))
            prices = prices_dict.get(market_id)
            if prices:
                self.current_prices[market_id] = prices.get("yes", 0)

        # Update correlation trackers for all pairs
        market_ids = list(self.current_prices.keys())

        for i in range(len(market_ids)):
            for j in range(i + 1, len(market_ids)):
                id1, id2 = market_ids[i], market_ids[j]
                pair_id = self._get_pair_id(id1, id2)

                if pair_id not in self.correlation_trackers:
                    self.correlation_trackers[pair_id] = CorrelationTracker(id1, id2)

                price1 = self.current_prices.get(id1, 0)
                price2 = self.current_prices.get(id2, 0)

                if price1 > 0 and price2 > 0:
                    self.correlation_trackers[pair_id].add_price_pair(price1, price2)

    def find_correlated_pairs(self) -> List[Tuple[str, str, float]]:
        """
        Find pairs of markets with high correlation

        Returns:
            List of (market_id_1, market_id_2, correlation) tuples
        """
        correlated_pairs = []

        for pair_id, tracker in self.correlation_trackers.items():
            correlation = tracker.calculate_correlation()

            if abs(correlation) >= self.min_correlation:
                correlated_pairs.append(
                    (tracker.market_id_1, tracker.market_id_2, correlation)
                )

        return correlated_pairs

    def analyze_pair(
        self, market_id_1: str, market_id_2: str, market_name_1: str, market_name_2: str
    ) -> Optional[StatisticalArbOpportunity]:
        """
        Analyze a pair of markets for statistical arbitrage opportunity

        Args:
            market_id_1: First market identifier
            market_id_2: Second market identifier
            market_name_1: First market name
            market_name_2: Second market name

        Returns:
            StatisticalArbOpportunity if found, None otherwise
        """
        pair_id = self._get_pair_id(market_id_1, market_id_2)

        if pair_id not in self.correlation_trackers:
            return None

        tracker = self.correlation_trackers[pair_id]

        # Calculate correlation
        correlation = tracker.calculate_correlation()

        if abs(correlation) < self.min_correlation:
            return None

        # Get current prices
        price_1 = self.current_prices.get(market_id_1, 0)
        price_2 = self.current_prices.get(market_id_2, 0)

        if price_1 == 0 or price_2 == 0:
            return None

        # Calculate divergence
        avg_price = (price_1 + price_2) / 2
        if avg_price == 0:
            return None
        divergence_pct = abs((price_1 - price_2) / avg_price) * 100

        if divergence_pct < self.min_divergence_pct:
            return None

        # Calculate z-score
        z_score = tracker.calculate_z_score(price_1, price_2)

        if abs(z_score) < self.min_z_score:
            return None

        # Determine direction
        direction = "market1_high" if price_1 > price_2 else "market2_high"

        # Create opportunity
        opportunity = StatisticalArbOpportunity(
            market_id_1=market_id_1,
            market_name_1=market_name_1,
            market_id_2=market_id_2,
            market_name_2=market_name_2,
            correlation=correlation,
            divergence_pct=divergence_pct,
            z_score=z_score,
            direction=direction,
            price_1=price_1,
            price_2=price_2,
        )

        return opportunity

    def find_opportunities(
        self, markets: List[Dict[str, Any]], prices_dict: Dict[str, Dict[str, float]]
    ) -> List[StatisticalArbOpportunity]:
        """
        Find all statistical arbitrage opportunities

        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data

        Returns:
            List of valid statistical arbitrage opportunities
        """
        opportunities = []

        # Update price tracking
        self.update_market_prices(markets, prices_dict)

        # Find correlated pairs
        correlated_pairs = self.find_correlated_pairs()

        # Create market name lookup
        market_names = {
            m.get("id", m.get("market_id", "unknown")): m.get(
                "question", m.get("name", "unknown")
            )
            for m in markets
        }

        # Analyze each correlated pair
        for id1, id2, correlation in correlated_pairs:
            name1 = market_names.get(id1, id1)
            name2 = market_names.get(id2, id2)

            opportunity = self.analyze_pair(id1, id2, name1, name2)

            if opportunity:
                opportunities.append(opportunity)
                self.opportunities_found += 1

                # Log the opportunity
                self.logger.log_opportunity(
                    market=f"{name1} vs {name2}",
                    yes_price=opportunity.price_1,
                    no_price=opportunity.price_2,
                    action_taken=f"{self.strategy_name}_detected_corr{correlation:.2f}_div{opportunity.divergence_pct:.1f}%",
                )

        return opportunities

    def analyze(
        self, market_data: Dict[str, Any], price_data: Dict[str, float]
    ) -> None:
        """
        Analyze is not used for pair-based strategy
        Use find_opportunities instead which analyzes all pairs
        """
        pass

    def should_enter(self, opportunity: StatisticalArbOpportunity) -> bool:
        """
        Determine if we should enter a position on this opportunity

        Args:
            opportunity: StatisticalArbOpportunity to evaluate

        Returns:
            True if should enter position, False otherwise
        """
        pair_id = opportunity.get_pair_id()

        # Don't enter if we already have a position on this pair
        if pair_id in self.active_positions:
            return False

        # Check correlation meets threshold
        if abs(opportunity.correlation) < self.min_correlation:
            return False

        # Check divergence meets threshold
        if opportunity.divergence_pct < self.min_divergence_pct:
            return False

        # Check z-score meets threshold
        if abs(opportunity.z_score) < self.min_z_score:
            return False

        return True

    def should_exit(self, pair_id: str) -> Tuple[bool, str]:
        """
        Determine if we should exit a position

        Args:
            pair_id: Pair identifier

        Returns:
            Tuple of (should_exit, reason)
        """
        # Check if we have an active position
        if pair_id not in self.active_positions:
            return False, ""

        position = self.active_positions[pair_id]

        market_id_1 = position["market_id_1"]
        market_id_2 = position["market_id_2"]
        entry_price_1 = position["entry_price_1"]
        entry_price_2 = position["entry_price_2"]
        direction = position["direction"]

        # Get current prices
        current_price_1 = self.current_prices.get(market_id_1, 0)
        current_price_2 = self.current_prices.get(market_id_2, 0)

        if current_price_1 == 0 or current_price_2 == 0:
            return False, ""

        # Get correlation tracker
        tracker = self.correlation_trackers.get(pair_id)
        if not tracker:
            return True, "no_tracker"

        # Calculate current correlation
        current_correlation = tracker.calculate_correlation()

        # Check for correlation breakdown
        if abs(current_correlation) < self.correlation_breakdown_threshold:
            return True, "correlation_breakdown"

        # Calculate current z-score
        z_score = tracker.calculate_z_score(current_price_1, current_price_2)

        # Check for convergence
        if abs(z_score) < self.exit_z_score:
            return True, "convergence"

        # Calculate profit/loss
        entry_spread = entry_price_1 - entry_price_2
        current_spread = current_price_1 - current_price_2

        if direction == "market1_high":
            # We bet market1 will decrease or market2 will increase
            # Profit when spread decreases
            spread_change_pct = (
                (entry_spread - current_spread) / abs(entry_spread)
            ) * 100
        else:  # market2_high
            # We bet market2 will decrease or market1 will increase
            # Profit when spread increases (becomes less negative)
            spread_change_pct = (
                (current_spread - entry_spread) / abs(entry_spread)
            ) * 100

        # Check profit target
        if spread_change_pct >= self.profit_target_pct:
            return True, "profit_target"

        # Check stop loss
        if spread_change_pct <= -self.stop_loss_pct:
            return True, "stop_loss"

        return False, ""

    def enter_position(
        self, opportunity: StatisticalArbOpportunity, trade_size: float
    ) -> TradeSignal:
        """Return a trade signal (signal-only; no execution or state mutation)."""
        pair_id = opportunity.get_pair_id()
        price = opportunity.price_1 or 0.5
        quantity = trade_size / price if price > 0 else 0
        return TradeSignal(
            symbol=pair_id,
            side="buy",
            quantity=quantity,
            order_type="market",
            price=price,
            strategy_name=self.strategy_name,
        )

    def exit_position(self, pair_id: str, reason: str = "manual") -> TradeSignal:
        """Return a sell signal (signal-only; no execution or state mutation)."""
        if pair_id not in self.active_positions:
            return TradeSignal(
                symbol=pair_id,
                side="sell",
                quantity=0,
                order_type="market",
                price=0.5,
                strategy_name=self.strategy_name,
            )
        position = self.active_positions[pair_id]
        entry_price_1 = position.get("entry_price_1") or 0.5
        quantity = (position["trade_size"] / entry_price_1) if entry_price_1 > 0 else 0
        price = self.current_prices.get(position["market_id_1"], 0.5)
        return TradeSignal(
            symbol=pair_id,
            side="sell",
            quantity=quantity,
            order_type="market",
            price=price,
            strategy_name=self.strategy_name,
        )

    def _get_pair_id(self, market_id_1: str, market_id_2: str) -> str:
        """Get unique identifier for a pair (order-independent)"""
        ids = sorted([market_id_1, market_id_2])
        return f"{ids[0]}_{ids[1]}"

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get strategy statistics

        Returns:
            Dictionary with strategy statistics
        """
        total_trades = self.opportunities_taken
        net_profit = self.total_profit - self.total_loss

        # Calculate actual win rate (would need to track winning vs losing trades separately)
        # For now, use profit ratio as an approximation
        if self.total_profit + self.total_loss > 0:
            profit_ratio = (
                self.total_profit / (self.total_profit + self.total_loss)
            ) * 100
        else:
            profit_ratio = 0.0

        return {
            "strategy_name": self.strategy_name,
            "opportunities_found": self.opportunities_found,
            "opportunities_taken": self.opportunities_taken,
            "total_profit": self.total_profit,
            "total_loss": self.total_loss,
            "net_profit": net_profit,
            "active_positions": len(self.active_positions),
            "tracked_pairs": len(self.correlation_trackers),
            "profit_ratio": profit_ratio,
        }

    def reset_statistics(self) -> None:
        """Reset strategy statistics"""
        self.opportunities_found = 0
        self.opportunities_taken = 0
        self.total_profit = 0.0
        self.total_loss = 0.0

    def get_name(self) -> str:
        """
        Get strategy name

        Returns:
            Strategy name string
        """
        return self.strategy_name
