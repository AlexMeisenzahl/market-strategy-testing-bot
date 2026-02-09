"""
Mean Reversion Strategy Module

Identifies when prices deviate significantly from their moving average
and trades expecting them to revert to the mean. Works best in ranging markets.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
from logger import get_logger


class PriceTracker:
    """Track price history for mean reversion calculations"""

    def __init__(self, max_history: int = 100):
        """
        Initialize price tracker

        Args:
            max_history: Maximum number of price points to track
        """
        self.prices: deque = deque(maxlen=max_history)

    def add_price(self, price: float, timestamp: Optional[datetime] = None) -> None:
        """Add a new price data point"""
        if timestamp is None:
            timestamp = datetime.now()
        self.prices.append((timestamp, price))

    def get_moving_average(self, window: int) -> Optional[float]:
        """
        Calculate moving average over window periods

        Args:
            window: Number of periods to average

        Returns:
            Moving average or None if insufficient data
        """
        if len(self.prices) < window:
            return None

        recent_prices = list(self.prices)[-window:]
        return sum(p[1] for p in recent_prices) / window

    def get_standard_deviation(self, window: int) -> Optional[float]:
        """
        Calculate standard deviation over window periods

        Args:
            window: Number of periods

        Returns:
            Standard deviation or None if insufficient data
        """
        if len(self.prices) < window:
            return None

        recent_prices = [p[1] for p in list(self.prices)[-window:]]
        mean = sum(recent_prices) / window
        variance = sum((x - mean) ** 2 for x in recent_prices) / window
        return variance**0.5

    def get_current_price(self) -> Optional[float]:
        """Get the most recent price"""
        if not self.prices:
            return None
        return self.prices[-1][1]


class MeanReversionOpportunity:
    """Represents a mean reversion trading opportunity"""

    def __init__(
        self,
        market_id: str,
        market_name: str,
        direction: str,
        current_price: float,
        moving_average: float,
        deviation_pct: float,
        z_score: float,
        confidence: str,
    ):
        """
        Initialize mean reversion opportunity

        Args:
            market_id: Unique market identifier
            market_name: Human-readable market name
            direction: 'long' (buy expecting price to rise) or 'short' (sell expecting price to fall)
            current_price: Current market price
            moving_average: Moving average price
            deviation_pct: Deviation from MA as percentage
            z_score: Number of standard deviations from mean
            confidence: 'medium', 'high', or 'very_high'
        """
        self.market_id = market_id
        self.market_name = market_name
        self.direction = direction
        self.current_price = current_price
        self.moving_average = moving_average
        self.deviation_pct = deviation_pct
        self.z_score = z_score
        self.confidence = confidence
        self.detected_at = datetime.now()
        self.opportunity_type = "mean_reversion"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "market_id": self.market_id,
            "market_name": self.market_name,
            "direction": self.direction,
            "current_price": self.current_price,
            "moving_average": self.moving_average,
            "deviation_pct": round(self.deviation_pct, 2),
            "z_score": round(self.z_score, 2),
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
            "type": self.opportunity_type,
        }


class MeanReversionStrategy:
    """
    Mean Reversion Strategy

    Trades when prices deviate significantly from their moving average,
    expecting them to revert back to the mean.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mean reversion strategy

        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.logger = get_logger()

        # Strategy parameters with defaults
        self.ma_window = config.get("ma_window", 20)
        self.min_deviation_pct = config.get("min_deviation_pct", 10.0)
        self.z_score_threshold = config.get("z_score_threshold", 2.0)
        self.max_holding_time = config.get("max_holding_time", 3600)

        # Track price history for each market
        self.price_trackers: Dict[str, PriceTracker] = {}

        self.logger.log_info(
            f"Mean Reversion Strategy initialized (MA window: {self.ma_window}, "
            f"min deviation: {self.min_deviation_pct}%, z-score: {self.z_score_threshold})"
        )

    def _get_or_create_tracker(self, market_id: str) -> PriceTracker:
        """Get or create price tracker for a market"""
        if market_id not in self.price_trackers:
            self.price_trackers[market_id] = PriceTracker()
        return self.price_trackers[market_id]

    def analyze(
        self, market_data: Dict, price_data: Dict
    ) -> Optional[MeanReversionOpportunity]:
        """
        Analyze a single market for mean reversion opportunities

        Args:
            market_data: Market metadata
            price_data: Current price information

        Returns:
            MeanReversionOpportunity if found, None otherwise
        """
        try:
            market_id = market_data.get("id", "unknown")
            market_name = market_data.get("question", "Unknown Market")

            # Get current YES price
            yes_price = price_data.get("yes_price", 0.0)
            if yes_price <= 0 or yes_price >= 1:
                return None

            # Update price tracker
            tracker = self._get_or_create_tracker(market_id)
            tracker.add_price(yes_price)

            # Calculate moving average
            ma = tracker.get_moving_average(self.ma_window)
            if ma is None:
                return None  # Not enough data yet

            # Calculate deviation from MA
            deviation = yes_price - ma
            deviation_pct = (deviation / ma) * 100

            # Check if deviation is significant enough
            if abs(deviation_pct) < self.min_deviation_pct:
                return None

            # Calculate z-score
            std_dev = tracker.get_standard_deviation(self.ma_window)
            if std_dev is None or std_dev == 0:
                return None

            z_score = deviation / std_dev

            # Check if z-score meets threshold
            if abs(z_score) < self.z_score_threshold:
                return None

            # Determine direction and confidence
            if deviation < 0:
                # Price below MA, expect it to rise (go long)
                direction = "long"
            else:
                # Price above MA, expect it to fall (go short)
                direction = "short"

            # Determine confidence based on z-score magnitude
            if abs(z_score) >= 3.0:
                confidence = "very_high"
            elif abs(z_score) >= 2.5:
                confidence = "high"
            else:
                confidence = "medium"

            return MeanReversionOpportunity(
                market_id=market_id,
                market_name=market_name,
                direction=direction,
                current_price=yes_price,
                moving_average=ma,
                deviation_pct=deviation_pct,
                z_score=z_score,
                confidence=confidence,
            )

        except Exception as e:
            self.logger.log_error(
                f"Error analyzing mean reversion for {market_data.get('question', 'unknown')}: {str(e)}"
            )
            return None

    def find_opportunities(
        self, markets: List[Dict], prices_dict: Dict
    ) -> List[MeanReversionOpportunity]:
        """
        Find mean reversion opportunities across all markets

        Args:
            markets: List of market data dictionaries
            prices_dict: Dictionary mapping market IDs to price data

        Returns:
            List of MeanReversionOpportunity objects
        """
        opportunities = []

        for market in markets:
            market_id = market.get("id", "unknown")
            price_data = prices_dict.get(market_id, {})

            if not price_data:
                continue

            opportunity = self.analyze(market, price_data)
            if opportunity:
                opportunities.append(opportunity)

        if opportunities:
            self.logger.log_info(
                f"Found {len(opportunities)} mean reversion opportunities"
            )

        return opportunities

    def should_exit(
        self, position: Dict, current_price_data: Dict, entry_price: float
    ) -> Tuple[bool, str]:
        """
        Determine if a mean reversion position should be exited

        Args:
            position: Position information
            current_price_data: Current market price data
            entry_price: Price at which position was entered

        Returns:
            Tuple of (should_exit: bool, reason: str)
        """
        try:
            market_id = position.get("market_id")
            direction = position.get("direction")
            current_price = current_price_data.get("yes_price", 0.0)

            if current_price <= 0:
                return False, ""

            # Get tracker and calculate current MA
            tracker = self._get_or_create_tracker(market_id)
            ma = tracker.get_moving_average(self.ma_window)

            if ma is None:
                return False, ""

            # Exit if price has reverted to MA (within 2%)
            deviation_from_ma = abs((current_price - ma) / ma) * 100
            if deviation_from_ma < 2.0:
                return True, "Price reverted to MA"

            # Exit on profit target (10% move toward MA)
            if direction == "long":
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                if profit_pct >= 10:
                    return True, "Profit target hit"
            else:  # short
                profit_pct = ((entry_price - current_price) / entry_price) * 100
                if profit_pct >= 10:
                    return True, "Profit target hit"

            # Exit on stop loss (5% move against position)
            if direction == "long":
                loss_pct = ((entry_price - current_price) / entry_price) * 100
                if loss_pct >= 5:
                    return True, "Stop loss triggered"
            else:  # short
                loss_pct = ((current_price - entry_price) / entry_price) * 100
                if loss_pct >= 5:
                    return True, "Stop loss triggered"

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
