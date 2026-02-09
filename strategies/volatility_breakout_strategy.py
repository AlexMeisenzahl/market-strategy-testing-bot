"""
Volatility Breakout Strategy Module

Detects when price breaks out of a low-volatility consolidation period,
indicating the start of a new trend. Trades in the direction of the breakout.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
from logger import get_logger


class VolatilityTracker:
    """Track price volatility and detect breakouts"""

    def __init__(self, max_history: int = 200):
        """
        Initialize volatility tracker

        Args:
            max_history: Maximum number of price points to track
        """
        self.high_prices: deque = deque(maxlen=max_history)
        self.low_prices: deque = deque(maxlen=max_history)
        self.close_prices: deque = deque(maxlen=max_history)
        self.timestamps: deque = deque(maxlen=max_history)

    def add_price(
        self,
        high: float,
        low: float,
        close: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Add new price data"""
        if timestamp is None:
            timestamp = datetime.now()

        self.high_prices.append(high)
        self.low_prices.append(low)
        self.close_prices.append(close)
        self.timestamps.append(timestamp)

    def get_bollinger_bands(
        self, window: int = 20, num_std: float = 2.0
    ) -> Optional[Tuple[float, float, float]]:
        """
        Calculate Bollinger Bands

        Args:
            window: Period for moving average
            num_std: Number of standard deviations for bands

        Returns:
            Tuple of (upper_band, middle_band, lower_band) or None if insufficient data
        """
        if len(self.close_prices) < window:
            return None

        recent_closes = list(self.close_prices)[-window:]
        middle = sum(recent_closes) / window

        # Calculate standard deviation
        variance = sum((x - middle) ** 2 for x in recent_closes) / window
        std_dev = variance ** 0.5

        upper = middle + (num_std * std_dev)
        lower = middle - (num_std * std_dev)

        return (upper, middle, lower)

    def get_atr(self, window: int = 14) -> Optional[float]:
        """
        Calculate Average True Range (volatility measure)

        Args:
            window: Period for ATR calculation

        Returns:
            ATR value or None if insufficient data
        """
        if len(self.close_prices) < window + 1:
            return None

        true_ranges = []
        for i in range(1, len(self.close_prices)):
            high = self.high_prices[i]
            low = self.low_prices[i]
            prev_close = self.close_prices[i - 1]

            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            true_ranges.append(max(tr1, tr2, tr3))

        if len(true_ranges) < window:
            return None

        recent_trs = true_ranges[-window:]
        return sum(recent_trs) / window

    def get_current_volatility_state(self) -> Optional[str]:
        """
        Determine current volatility state

        Returns:
            'low', 'normal', 'high', or None if insufficient data
        """
        atr = self.get_atr(14)
        if atr is None:
            return None

        # Get long-term ATR for comparison
        long_atr = self.get_atr(50)
        if long_atr is None:
            return None

        ratio = atr / long_atr if long_atr > 0 else 1.0

        if ratio < 0.7:
            return "low"
        elif ratio > 1.3:
            return "high"
        else:
            return "normal"


class VolatilityBreakoutOpportunity:
    """Represents a volatility breakout trading opportunity"""

    def __init__(
        self,
        market_id: str,
        market_name: str,
        direction: str,
        current_price: float,
        breakout_level: float,
        volatility_state: str,
        atr: float,
        confidence: str,
    ):
        """
        Initialize volatility breakout opportunity

        Args:
            market_id: Unique market identifier
            market_name: Human-readable market name
            direction: 'long' (bullish breakout) or 'short' (bearish breakout)
            current_price: Current market price
            breakout_level: Price level that was broken
            volatility_state: Current volatility state
            atr: Average True Range value
            confidence: 'medium', 'high', or 'very_high'
        """
        self.market_id = market_id
        self.market_name = market_name
        self.direction = direction
        self.current_price = current_price
        self.breakout_level = breakout_level
        self.volatility_state = volatility_state
        self.atr = atr
        self.confidence = confidence
        self.detected_at = datetime.now()
        self.opportunity_type = "volatility_breakout"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "market_id": self.market_id,
            "market_name": self.market_name,
            "direction": self.direction,
            "current_price": self.current_price,
            "breakout_level": self.breakout_level,
            "volatility_state": self.volatility_state,
            "atr": round(self.atr, 4),
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
            "type": self.opportunity_type,
        }


class VolatilityBreakoutStrategy:
    """
    Volatility Breakout Strategy

    Detects when price breaks out from a consolidation period (low volatility)
    into expansion (high volatility), trading in the direction of the breakout.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize volatility breakout strategy

        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.logger = get_logger()

        # Strategy parameters with defaults
        self.bb_window = config.get("bb_window", 20)
        self.bb_num_std = config.get("bb_num_std", 2.0)
        self.min_consolidation_periods = config.get("min_consolidation_periods", 10)
        self.breakout_threshold_pct = config.get("breakout_threshold_pct", 1.0)
        self.max_holding_time = config.get("max_holding_time", 1800)

        # Track volatility for each market
        self.volatility_trackers: Dict[str, VolatilityTracker] = {}

        self.logger.log_info(
            f"Volatility Breakout Strategy initialized (BB window: {self.bb_window}, "
            f"breakout threshold: {self.breakout_threshold_pct}%)"
        )

    def _get_or_create_tracker(self, market_id: str) -> VolatilityTracker:
        """Get or create volatility tracker for a market"""
        if market_id not in self.volatility_trackers:
            self.volatility_trackers[market_id] = VolatilityTracker()
        return self.volatility_trackers[market_id]

    def analyze(
        self, market_data: Dict, price_data: Dict
    ) -> Optional[VolatilityBreakoutOpportunity]:
        """
        Analyze a single market for volatility breakout opportunities

        Args:
            market_data: Market metadata
            price_data: Current price information

        Returns:
            VolatilityBreakoutOpportunity if found, None otherwise
        """
        try:
            market_id = market_data.get("id", "unknown")
            market_name = market_data.get("question", "Unknown Market")

            # Get current prices
            yes_price = price_data.get("yes_price", 0.0)
            no_price = price_data.get("no_price", 0.0)

            if yes_price <= 0 or yes_price >= 1:
                return None

            # For prediction markets, we use YES price as "close"
            # and estimate high/low based on bid/ask spread
            spread = abs(yes_price - no_price) / 2 if no_price > 0 else 0.01
            high = yes_price + spread
            low = yes_price - spread

            # Update volatility tracker
            tracker = self._get_or_create_tracker(market_id)
            tracker.add_price(high=high, low=low, close=yes_price)

            # Get Bollinger Bands
            bands = tracker.get_bollinger_bands(self.bb_window, self.bb_num_std)
            if bands is None:
                return None  # Not enough data

            upper_band, middle_band, lower_band = bands

            # Get ATR for volatility measurement
            atr = tracker.get_atr(14)
            if atr is None:
                return None

            # Get volatility state
            vol_state = tracker.get_current_volatility_state()
            if vol_state is None:
                return None

            # Look for breakout from consolidation
            # Price should break out of Bollinger Bands after low volatility period
            direction = None
            breakout_level = None
            confidence = "medium"

            # Check for bullish breakout (price above upper band)
            if yes_price > upper_band:
                breakout_distance = ((yes_price - upper_band) / upper_band) * 100
                if breakout_distance >= self.breakout_threshold_pct:
                    direction = "long"
                    breakout_level = upper_band

                    # Higher confidence if breaking out from low volatility
                    if vol_state == "low":
                        confidence = "very_high"
                    elif vol_state == "normal":
                        confidence = "high"

            # Check for bearish breakout (price below lower band)
            elif yes_price < lower_band:
                breakout_distance = ((lower_band - yes_price) / lower_band) * 100
                if breakout_distance >= self.breakout_threshold_pct:
                    direction = "short"
                    breakout_level = lower_band

                    # Higher confidence if breaking out from low volatility
                    if vol_state == "low":
                        confidence = "very_high"
                    elif vol_state == "normal":
                        confidence = "high"

            if direction is None:
                return None

            return VolatilityBreakoutOpportunity(
                market_id=market_id,
                market_name=market_name,
                direction=direction,
                current_price=yes_price,
                breakout_level=breakout_level,
                volatility_state=vol_state,
                atr=atr,
                confidence=confidence,
            )

        except Exception as e:
            self.logger.log_error(
                f"Error analyzing volatility breakout for {market_data.get('question', 'unknown')}: {str(e)}"
            )
            return None

    def find_opportunities(
        self, markets: List[Dict], prices_dict: Dict
    ) -> List[VolatilityBreakoutOpportunity]:
        """
        Find volatility breakout opportunities across all markets

        Args:
            markets: List of market data dictionaries
            prices_dict: Dictionary mapping market IDs to price data

        Returns:
            List of VolatilityBreakoutOpportunity objects
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
                f"Found {len(opportunities)} volatility breakout opportunities"
            )

        return opportunities

    def should_exit(
        self, position: Dict, current_price_data: Dict, entry_price: float
    ) -> Tuple[bool, str]:
        """
        Determine if a volatility breakout position should be exited

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

            # Get tracker for Bollinger Bands
            tracker = self._get_or_create_tracker(market_id)
            bands = tracker.get_bollinger_bands(self.bb_window, self.bb_num_std)

            if bands is None:
                return False, ""

            upper_band, middle_band, lower_band = bands

            # Exit if price reverts back inside bands
            if direction == "long" and current_price < middle_band:
                return True, "Price reverted to middle band"
            elif direction == "short" and current_price > middle_band:
                return True, "Price reverted to middle band"

            # Exit on profit target (15% move)
            if direction == "long":
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                if profit_pct >= 15:
                    return True, "Profit target hit"
            else:  # short
                profit_pct = ((entry_price - current_price) / entry_price) * 100
                if profit_pct >= 15:
                    return True, "Profit target hit"

            # Exit on stop loss (7% adverse move)
            if direction == "long":
                loss_pct = ((entry_price - current_price) / entry_price) * 100
                if loss_pct >= 7:
                    return True, "Stop loss triggered"
            else:  # short
                loss_pct = ((current_price - entry_price) / entry_price) * 100
                if loss_pct >= 7:
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
