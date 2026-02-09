"""
Pairs Trading Strategy Module

Simplified pairs trading that identifies correlated prediction markets
and trades when they diverge, expecting convergence. Different from
statistical_arb_strategy in that it focuses on binary relationships
rather than complex multi-market correlations.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict
from logger import get_logger


# Common stop words to filter out when comparing market names
STOP_WORDS = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'will', 'be', 'by'}


class PairTracker:
    """Track price history for a pair of markets"""

    def __init__(self, max_history: int = 100):
        """
        Initialize pair tracker

        Args:
            max_history: Maximum number of data points to track
        """
        self.market1_prices: deque = deque(maxlen=max_history)
        self.market2_prices: deque = deque(maxlen=max_history)
        self.timestamps: deque = deque(maxlen=max_history)

    def add_prices(
        self, market1_price: float, market2_price: float, timestamp: Optional[datetime] = None
    ) -> None:
        """Add price data for both markets"""
        if timestamp is None:
            timestamp = datetime.now()

        self.market1_prices.append(market1_price)
        self.market2_prices.append(market2_price)
        self.timestamps.append(timestamp)

    def calculate_correlation(self, window: Optional[int] = None) -> Optional[float]:
        """
        Calculate correlation coefficient between the two markets

        Args:
            window: Number of periods to use (None = all available)

        Returns:
            Correlation coefficient (-1 to 1) or None if insufficient data
        """
        if len(self.market1_prices) < 10:  # Need minimum data points
            return None

        # Use specified window or all data
        if window and window < len(self.market1_prices):
            prices1 = list(self.market1_prices)[-window:]
            prices2 = list(self.market2_prices)[-window:]
        else:
            prices1 = list(self.market1_prices)
            prices2 = list(self.market2_prices)

        if len(prices1) < 10:
            return None

        # Calculate means
        mean1 = sum(prices1) / len(prices1)
        mean2 = sum(prices2) / len(prices2)

        # Calculate correlation
        numerator = sum((x - mean1) * (y - mean2) for x, y in zip(prices1, prices2))
        sum_sq1 = sum((x - mean1) ** 2 for x in prices1)
        sum_sq2 = sum((y - mean2) ** 2 for y in prices2)

        denominator = (sum_sq1 * sum_sq2) ** 0.5

        if denominator == 0:
            return None

        return numerator / denominator

    def calculate_spread(self) -> Optional[float]:
        """
        Calculate current price spread between markets

        Returns:
            Spread as percentage or None if no data
        """
        if not self.market1_prices or not self.market2_prices:
            return None

        current_spread = self.market1_prices[-1] - self.market2_prices[-1]
        return current_spread

    def calculate_spread_zscore(self, window: int = 20) -> Optional[float]:
        """
        Calculate z-score of current spread

        Args:
            window: Period for calculation

        Returns:
            Z-score or None if insufficient data
        """
        if len(self.market1_prices) < window:
            return None

        # Calculate recent spreads
        recent1 = list(self.market1_prices)[-window:]
        recent2 = list(self.market2_prices)[-window:]
        spreads = [p1 - p2 for p1, p2 in zip(recent1, recent2)]

        # Calculate mean and std dev of spreads
        mean_spread = sum(spreads) / len(spreads)
        variance = sum((s - mean_spread) ** 2 for s in spreads) / len(spreads)
        std_spread = variance ** 0.5

        if std_spread == 0:
            return None

        current_spread = spreads[-1]
        z_score = (current_spread - mean_spread) / std_spread

        return z_score


class PairsTradingOpportunity:
    """Represents a pairs trading opportunity"""

    def __init__(
        self,
        market1_id: str,
        market1_name: str,
        market1_price: float,
        market2_id: str,
        market2_name: str,
        market2_price: float,
        spread: float,
        z_score: float,
        correlation: float,
        direction: str,
        confidence: str,
    ):
        """
        Initialize pairs trading opportunity

        Args:
            market1_id: First market ID
            market1_name: First market name
            market1_price: First market price
            market2_id: Second market ID
            market2_name: Second market name
            market2_price: Second market price
            spread: Current price spread
            z_score: Z-score of spread
            correlation: Correlation coefficient
            direction: 'long1_short2' or 'short1_long2'
            confidence: 'medium', 'high', or 'very_high'
        """
        self.market1_id = market1_id
        self.market1_name = market1_name
        self.market1_price = market1_price
        self.market2_id = market2_id
        self.market2_name = market2_name
        self.market2_price = market2_price
        self.spread = spread
        self.z_score = z_score
        self.correlation = correlation
        self.direction = direction
        self.confidence = confidence
        self.detected_at = datetime.now()
        self.opportunity_type = "pairs_trading"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "market1_id": self.market1_id,
            "market1_name": self.market1_name,
            "market1_price": self.market1_price,
            "market2_id": self.market2_id,
            "market2_name": self.market2_name,
            "market2_price": self.market2_price,
            "spread": round(self.spread, 4),
            "z_score": round(self.z_score, 2),
            "correlation": round(self.correlation, 2),
            "direction": self.direction,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
            "type": self.opportunity_type,
        }


class PairsTradingStrategy:
    """
    Pairs Trading Strategy

    Identifies correlated markets and trades when their prices diverge,
    expecting them to converge back to their historical relationship.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize pairs trading strategy

        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.logger = get_logger()

        # Strategy parameters with defaults
        self.min_correlation = config.get("min_correlation", 0.7)
        self.z_score_threshold = config.get("z_score_threshold", 2.0)
        self.spread_window = config.get("spread_window", 20)
        self.max_holding_time = config.get("max_holding_time", 3600)

        # Track pairs
        self.pair_trackers: Dict[Tuple[str, str], PairTracker] = {}

        self.logger.log_info(
            f"Pairs Trading Strategy initialized (min correlation: {self.min_correlation}, "
            f"z-score threshold: {self.z_score_threshold})"
        )

    def _get_pair_key(self, market1_id: str, market2_id: str) -> Tuple[str, str]:
        """Get consistent pair key regardless of order"""
        return tuple(sorted([market1_id, market2_id]))

    def _get_or_create_tracker(
        self, market1_id: str, market2_id: str
    ) -> PairTracker:
        """Get or create pair tracker"""
        pair_key = self._get_pair_key(market1_id, market2_id)
        if pair_key not in self.pair_trackers:
            self.pair_trackers[pair_key] = PairTracker()
        return self.pair_trackers[pair_key]

    def _are_markets_related(self, market1_name: str, market2_name: str) -> bool:
        """
        Check if markets are potentially related based on name similarity

        Args:
            market1_name: First market name
            market2_name: Second market name

        Returns:
            True if markets might be related
        """
        # Convert to lowercase for comparison
        name1 = market1_name.lower()
        name2 = market2_name.lower()

        # Check for common keywords
        keywords1 = set(name1.split())
        keywords2 = set(name2.split())

        # Markets are related if they share significant keywords
        common_words = keywords1.intersection(keywords2)
        
        # Filter out common words
        meaningful_common = common_words - STOP_WORDS

        # Need at least 2 meaningful common words or 30% overlap
        if len(meaningful_common) >= 2:
            return True

        overlap_pct = len(common_words) / max(len(keywords1), len(keywords2))
        return overlap_pct >= 0.3

    def analyze_pair(
        self,
        market1: Dict,
        market1_price_data: Dict,
        market2: Dict,
        market2_price_data: Dict,
    ) -> Optional[PairsTradingOpportunity]:
        """
        Analyze a pair of markets for trading opportunities

        Args:
            market1: First market data
            market1_price_data: First market price data
            market2: Second market data
            market2_price_data: Second market price data

        Returns:
            PairsTradingOpportunity if found, None otherwise
        """
        try:
            market1_id = market1.get("id", "unknown")
            market2_id = market2.get("id", "unknown")
            market1_name = market1.get("question", "Unknown")
            market2_name = market2.get("question", "Unknown")

            # Check if markets are potentially related
            if not self._are_markets_related(market1_name, market2_name):
                return None

            # Get prices
            market1_price = market1_price_data.get("yes_price", 0.0)
            market2_price = market2_price_data.get("yes_price", 0.0)

            if market1_price <= 0 or market1_price >= 1:
                return None
            if market2_price <= 0 or market2_price >= 1:
                return None

            # Update pair tracker
            tracker = self._get_or_create_tracker(market1_id, market2_id)
            tracker.add_prices(market1_price, market2_price)

            # Calculate correlation
            correlation = tracker.calculate_correlation()
            if correlation is None or abs(correlation) < self.min_correlation:
                return None

            # Calculate spread z-score
            z_score = tracker.calculate_spread_zscore(self.spread_window)
            if z_score is None or abs(z_score) < self.z_score_threshold:
                return None

            # Calculate current spread
            spread = tracker.calculate_spread()
            if spread is None:
                return None

            # Determine trade direction based on z-score
            # Positive z-score means market1 > market2 (diverged upward)
            # -> Short market1, Long market2 (expect convergence)
            if z_score > 0:
                direction = "short1_long2"
            else:
                direction = "long1_short2"

            # Determine confidence based on z-score and correlation
            if abs(z_score) >= 3.0 and abs(correlation) >= 0.85:
                confidence = "very_high"
            elif abs(z_score) >= 2.5 and abs(correlation) >= 0.75:
                confidence = "high"
            else:
                confidence = "medium"

            return PairsTradingOpportunity(
                market1_id=market1_id,
                market1_name=market1_name,
                market1_price=market1_price,
                market2_id=market2_id,
                market2_name=market2_name,
                market2_price=market2_price,
                spread=spread,
                z_score=z_score,
                correlation=correlation,
                direction=direction,
                confidence=confidence,
            )

        except Exception as e:
            self.logger.log_error(f"Error analyzing pair: {str(e)}")
            return None

    def find_opportunities(
        self, markets: List[Dict], prices_dict: Dict
    ) -> List[PairsTradingOpportunity]:
        """
        Find pairs trading opportunities across all market pairs

        Args:
            markets: List of market data dictionaries
            prices_dict: Dictionary mapping market IDs to price data

        Returns:
            List of PairsTradingOpportunity objects
        """
        opportunities = []

        # Analyze all unique pairs (this can be expensive for many markets)
        # In production, you might want to pre-filter or limit the pairs checked
        for i in range(len(markets)):
            for j in range(i + 1, min(i + 10, len(markets))):  # Limit pairs per market
                market1 = markets[i]
                market2 = markets[j]

                market1_id = market1.get("id", "unknown")
                market2_id = market2.get("id", "unknown")

                price1 = prices_dict.get(market1_id, {})
                price2 = prices_dict.get(market2_id, {})

                if not price1 or not price2:
                    continue

                opportunity = self.analyze_pair(market1, price1, market2, price2)
                if opportunity:
                    opportunities.append(opportunity)

        if opportunities:
            self.logger.log_info(
                f"Found {len(opportunities)} pairs trading opportunities"
            )

        return opportunities

    def should_exit(
        self,
        position: Dict,
        current_price1: float,
        current_price2: float,
        entry_spread: float,
    ) -> Tuple[bool, str]:
        """
        Determine if a pairs trading position should be exited

        Args:
            position: Position information
            current_price1: Current price of first market
            current_price2: Current price of second market
            entry_spread: Spread at entry

        Returns:
            Tuple of (should_exit: bool, reason: str)
        """
        try:
            market1_id = position.get("market1_id")
            market2_id = position.get("market2_id")

            # Get current spread
            current_spread = current_price1 - current_price2

            # Get tracker for z-score
            tracker = self._get_or_create_tracker(market1_id, market2_id)
            z_score = tracker.calculate_spread_zscore(self.spread_window)

            if z_score is None:
                return False, ""

            # Exit if spread has converged (z-score near 0)
            if abs(z_score) < 0.5:
                return True, "Spread converged"

            # Exit on profit target (spread moved 50% toward mean)
            spread_change = abs(current_spread - entry_spread)
            if spread_change >= abs(entry_spread) * 0.5:
                return True, "Profit target hit"

            # Exit if correlation breaks down
            correlation = tracker.calculate_correlation(window=50)
            if correlation is not None and abs(correlation) < 0.5:
                return True, "Correlation breakdown"

            # Exit if held too long
            entry_time = position.get("entry_time")
            if entry_time:
                hold_time = (datetime.now() - entry_time).total_seconds()
                if hold_time > self.max_holding_time:
                    return True, "Max holding time exceeded"

            return False, ""

        except Exception as e:
            self.logger.log_error(f"Error checking exit conditions: {str(e)}")
            return False, ""
