"""
News Strategy Module

Event-based trading strategy that detects and trades on breaking news events.
Monitors for sudden volume/volatility spikes and rapid price movements.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
from logger import get_logger
from engine import TradeSignal


class VolumeTracker:
    """Track volume data for spike detection"""

    def __init__(self, baseline_window: int = 300):
        """
        Initialize volume tracker

        Args:
            baseline_window: Window for calculating baseline volume (seconds)
        """
        self.volumes: deque = deque()  # [(timestamp, volume), ...]
        self.baseline_window = baseline_window

    def add_volume(self, volume: float) -> None:
        """Add a new volume data point"""
        self.volumes.append((datetime.now(), volume))
        self._clean_old_data()

    def _clean_old_data(self) -> None:
        """Remove data older than baseline window"""
        cutoff_time = datetime.now() - timedelta(seconds=self.baseline_window * 2)
        while self.volumes and self.volumes[0][0] < cutoff_time:
            self.volumes.popleft()

    def get_baseline_volume(self) -> float:
        """
        Calculate baseline volume (average over baseline window)

        Returns:
            Average volume
        """
        if not self.volumes:
            return 0.0

        cutoff_time = datetime.now() - timedelta(seconds=self.baseline_window)
        baseline_volumes = [v[1] for v in self.volumes if v[0] < cutoff_time]

        if not baseline_volumes:
            return 0.0

        return sum(baseline_volumes) / len(baseline_volumes)

    def get_recent_volume(self, window_seconds: int = 60) -> float:
        """
        Get average volume in recent time window

        Args:
            window_seconds: Time window in seconds

        Returns:
            Average volume in window
        """
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        recent_volumes = [v[1] for v in self.volumes if v[0] >= cutoff_time]

        if not recent_volumes:
            return 0.0

        return sum(recent_volumes) / len(recent_volumes)

    def detect_volume_spike(self, threshold_pct: float = 300.0) -> Tuple[bool, float]:
        """
        Detect if there's a volume spike

        Args:
            threshold_pct: Spike threshold as percentage of baseline

        Returns:
            Tuple of (is_spike, spike_magnitude_pct)
        """
        baseline = self.get_baseline_volume()
        if baseline == 0:
            return False, 0.0

        recent = self.get_recent_volume(60)  # Last minute
        spike_pct = ((recent - baseline) / baseline) * 100

        is_spike = spike_pct >= threshold_pct
        return is_spike, spike_pct


class NewsOpportunity:
    """Represents a news-based trading opportunity"""

    def __init__(
        self,
        market_id: str,
        market_name: str,
        direction: str,
        price_movement: float,
        volume_spike: float,
        volatility: float,
        current_price: float,
    ):
        """
        Initialize news opportunity

        Args:
            market_id: Unique market identifier
            market_name: Human-readable market name
            direction: 'bullish' or 'bearish'
            price_movement: Rapid price movement percentage
            volume_spike: Volume spike magnitude (%)
            volatility: Current volatility measure
            current_price: Current YES price
        """
        self.market_id = market_id
        self.market_name = market_name
        self.direction = direction
        self.price_movement = price_movement
        self.volume_spike = volume_spike
        self.volatility = volatility
        self.current_price = current_price
        self.detected_at = datetime.now()
        self.opportunity_type = "news"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "market_id": self.market_id,
            "market_name": self.market_name,
            "direction": self.direction,
            "price_movement": self.price_movement,
            "volume_spike": self.volume_spike,
            "volatility": self.volatility,
            "current_price": self.current_price,
            "opportunity_type": self.opportunity_type,
            "strategy": "crypto_news",
            "arbitrage_type": "N/A",
            "detected_at": self.detected_at.isoformat(),
        }


class NewsStrategy:
    """
    News-based event trading strategy

    Detects breaking news events through volume spikes and rapid price
    movements. Enters quickly on confirmed events and exits on profit
    targets or reversal signals.

    Entry Criteria:
    - Volume spike >300% in last minute
    - Price moved >5% rapidly
    - Direction clear (not choppy)

    Exit Criteria:
    - +15-40% profit target
    - -15% stop loss
    - Reversal signal detected
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize news strategy

        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.logger = get_logger()
        self.strategy_name = "crypto_news"

        # Strategy parameters
        self.min_volume_spike = config.get("news_min_volume_spike", 300.0)  # 300%
        self.min_price_movement = config.get("news_min_price_movement", 5.0)  # 5%
        self.profit_target_min = config.get("news_profit_target_min", 15.0)  # 15%
        self.profit_target_max = config.get("news_profit_target_max", 40.0)  # 40%
        self.stop_loss_pct = config.get("news_stop_loss", 15.0)  # 15%
        self.reversal_threshold = config.get("news_reversal_threshold", 3.0)  # 3%
        self.max_hold_time_minutes = config.get("news_max_hold_time", 30)  # 30 minutes

        # Volume tracking (market_id -> VolumeTracker)
        self.volume_trackers: Dict[str, VolumeTracker] = {}

        # Price tracking for rapid movement detection
        self.recent_prices: Dict[str, deque] = {}

        # Statistics tracking
        self.opportunities_found = 0
        self.opportunities_taken = 0
        self.total_profit = 0.0
        self.total_loss = 0.0

        # Active positions (market_id -> position info)
        self.active_positions: Dict[str, Dict[str, Any]] = {}

    def update_market_data(
        self, market_id: str, yes_price: float, no_price: float, volume: float = 0.0
    ) -> None:
        """
        Update market data for tracking

        Args:
            market_id: Market identifier
            yes_price: Current YES price
            no_price: Current NO price
            volume: Current volume
        """
        # Update volume tracker
        if market_id not in self.volume_trackers:
            self.volume_trackers[market_id] = VolumeTracker()
        self.volume_trackers[market_id].add_volume(volume)

        # Update price tracker
        if market_id not in self.recent_prices:
            self.recent_prices[market_id] = deque(maxlen=60)  # Keep last 60 data points
        self.recent_prices[market_id].append((datetime.now(), yes_price))

    def detect_rapid_price_movement(self, market_id: str) -> Tuple[float, str]:
        """
        Detect rapid price movement in last minute

        Args:
            market_id: Market identifier

        Returns:
            Tuple of (price_change_pct, direction)
        """
        if (
            market_id not in self.recent_prices
            or len(self.recent_prices[market_id]) < 2
        ):
            return 0.0, "neutral"

        prices = self.recent_prices[market_id]

        # Get price from 1 minute ago
        cutoff_time = datetime.now() - timedelta(seconds=60)
        old_prices = [p for p in prices if p[0] <= cutoff_time]

        if not old_prices:
            # Use oldest available price
            old_price = prices[0][1]
        else:
            old_price = old_prices[-1][1]

        current_price = prices[-1][1]

        if old_price == 0:
            return 0.0, "neutral"

        price_change = ((current_price - old_price) / old_price) * 100
        direction = (
            "bullish"
            if price_change > 0
            else "bearish" if price_change < 0 else "neutral"
        )

        return abs(price_change), direction

    def calculate_volatility(self, market_id: str) -> float:
        """
        Calculate recent volatility

        Args:
            market_id: Market identifier

        Returns:
            Volatility measure (standard deviation of price changes)
        """
        if (
            market_id not in self.recent_prices
            or len(self.recent_prices[market_id]) < 5
        ):
            return 0.0

        prices = list(self.recent_prices[market_id])

        # Calculate price changes
        changes = []
        for i in range(1, len(prices)):
            prev_price = prices[i - 1][1]
            if prev_price != 0 and prev_price is not None:
                change = ((prices[i][1] - prev_price) / prev_price) * 100
                changes.append(change)

        if not changes:
            return 0.0

        # Calculate standard deviation
        mean_change = sum(changes) / len(changes)
        variance = sum((x - mean_change) ** 2 for x in changes) / len(changes)
        volatility = variance**0.5

        return volatility

    def analyze(
        self, market_data: Dict[str, Any], price_data: Dict[str, float]
    ) -> Optional[NewsOpportunity]:
        """
        Analyze a market for news-based opportunities

        Args:
            market_data: Market information (id, name, etc.)
            price_data: Current prices {'yes': float, 'no': float, 'volume': float}

        Returns:
            NewsOpportunity if found, None otherwise
        """
        market_id = market_data.get("id", market_data.get("market_id", "unknown"))
        market_name = market_data.get("question", market_data.get("name", market_id))

        yes_price = price_data.get("yes", 0)
        no_price = price_data.get("no", 0)
        volume = price_data.get("volume", 0)

        # Update market data
        self.update_market_data(market_id, yes_price, no_price, volume)

        # Detect volume spike
        if market_id not in self.volume_trackers:
            return None

        is_volume_spike, volume_spike_pct = self.volume_trackers[
            market_id
        ].detect_volume_spike(self.min_volume_spike)

        if not is_volume_spike:
            return None

        # Detect rapid price movement
        price_movement, direction = self.detect_rapid_price_movement(market_id)

        if price_movement < self.min_price_movement or direction == "neutral":
            return None

        # Calculate volatility
        volatility = self.calculate_volatility(market_id)

        # Create opportunity
        opportunity = NewsOpportunity(
            market_id=market_id,
            market_name=market_name,
            direction=direction,
            price_movement=price_movement,
            volume_spike=volume_spike_pct,
            volatility=volatility,
            current_price=yes_price,
        )

        self.opportunities_found += 1

        # Log the opportunity
        self.logger.log_opportunity(
            market=market_name,
            yes_price=yes_price,
            no_price=no_price,
            action_taken=f"{self.strategy_name}_detected_{direction}_vol{volume_spike_pct:.0f}%",
        )

        return opportunity

    def find_opportunities(
        self, markets: List[Dict[str, Any]], prices_dict: Dict[str, Dict[str, float]]
    ) -> List[NewsOpportunity]:
        """
        Find all news opportunities across multiple markets

        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data

        Returns:
            List of valid news opportunities
        """
        opportunities = []

        for market in markets:
            market_id = market.get("id", market.get("market_id", "unknown"))
            prices = prices_dict.get(market_id)

            if not prices:
                continue

            opportunity = self.analyze(market, prices)
            if opportunity:
                opportunities.append(opportunity)

        return opportunities

    def should_enter(self, opportunity: NewsOpportunity) -> bool:
        """
        Determine if we should enter a position on this opportunity

        Args:
            opportunity: NewsOpportunity to evaluate

        Returns:
            True if should enter position, False otherwise
        """
        # Don't enter if we already have a position in this market
        if opportunity.market_id in self.active_positions:
            return False

        # Check volume spike meets threshold
        if opportunity.volume_spike < self.min_volume_spike:
            return False

        # Check price movement meets threshold
        if opportunity.price_movement < self.min_price_movement:
            return False

        # Check direction is clear (not neutral)
        if opportunity.direction == "neutral":
            return False

        return True

    def should_exit(
        self, market_id: str, current_prices: Dict[str, float]
    ) -> Tuple[bool, str]:
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
        entry_price = position["entry_price"]
        entry_time = position["entry_time"]
        direction = position["direction"]

        current_price = current_prices.get("yes", 0)

        # Calculate profit/loss
        if direction == "bullish":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # bearish
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        # Check stop loss
        if pnl_pct <= -self.stop_loss_pct:
            return True, "stop_loss"

        # Check profit target
        if pnl_pct >= self.profit_target_min:
            return True, "profit_target"

        # Check max hold time
        hold_time_minutes = (datetime.now() - entry_time).total_seconds() / 60
        if hold_time_minutes >= self.max_hold_time_minutes:
            return True, "max_hold_time"

        # Check for reversal
        price_movement, current_direction = self.detect_rapid_price_movement(market_id)

        # If direction has reversed significantly
        if direction == "bullish" and current_direction == "bearish":
            if price_movement >= self.reversal_threshold:
                return True, "reversal"
        elif direction == "bearish" and current_direction == "bullish":
            if price_movement >= self.reversal_threshold:
                return True, "reversal"

        return False, ""

    def enter_position(
        self, opportunity: NewsOpportunity, trade_size: float
    ) -> TradeSignal:
        """Return a trade signal (signal-only; no execution or state mutation)."""
        price = opportunity.current_price or 0.5
        quantity = trade_size / price if price > 0 else 0
        return TradeSignal(
            symbol=opportunity.market_id,
            side="buy",
            quantity=quantity,
            order_type="market",
            price=price,
            strategy_name=self.strategy_name,
        )

    def exit_position(
        self, market_id: str, exit_price: float, reason: str = "manual"
    ) -> TradeSignal:
        """Return a sell signal (signal-only; no execution or state mutation)."""
        if market_id not in self.active_positions:
            return TradeSignal(
                symbol=market_id,
                side="sell",
                quantity=0,
                order_type="market",
                price=exit_price,
                strategy_name=self.strategy_name,
            )
        position = self.active_positions[market_id]
        entry_price = position.get("entry_price") or 0.5
        quantity = (position["trade_size"] / entry_price) if entry_price > 0 else 0
        return TradeSignal(
            symbol=market_id,
            side="sell",
            quantity=quantity,
            order_type="market",
            price=exit_price,
            strategy_name=self.strategy_name,
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get strategy statistics

        Returns:
            Dictionary with strategy statistics
        """
        total_trades = self.opportunities_taken
        net_profit = self.total_profit - self.total_loss

        # Calculate profit ratio as approximation of win rate
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
