"""
Risk Manager

Enforces risk management rules and limits:
- Position sizing
- Position limits
- Daily loss limits
- Stop-loss auto-triggering
- Take-profit auto-triggering
- Portfolio exposure limits
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Risk management system for trading bot

    Enforces position limits, loss limits, and risk rules.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize risk manager

        Args:
            config: Configuration dictionary with risk settings
        """
        self.config = config
        risk_config = config.get("risk", {})

        # Risk limits
        self.max_position_size = risk_config.get("max_position_size", 1000)
        self.max_daily_loss = risk_config.get("max_daily_loss", 500)
        self.max_total_exposure = risk_config.get("max_total_exposure", 5000)
        self.max_positions = risk_config.get("max_positions", 10)

        # Position sizing
        self.default_position_pct = risk_config.get(
            "default_position_pct", 0.1
        )  # 10% of capital
        self.max_position_pct = risk_config.get(
            "max_position_pct", 0.2
        )  # 20% of capital

        # Stop-loss and take-profit
        self.default_stop_loss_pct = risk_config.get(
            "default_stop_loss_pct", 0.05
        )  # 5%
        self.default_take_profit_pct = risk_config.get(
            "default_take_profit_pct", 0.10
        )  # 10%

        # Daily tracking
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()

        # Position tracking
        self.open_positions: Dict[str, Dict[str, Any]] = {}

    def reset_daily_limits(self):
        """Reset daily loss tracking"""
        today = datetime.now().date()

        if today > self.last_reset_date:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.last_reset_date = today
            logger.info("Daily risk limits reset")

    def calculate_position_size(
        self,
        capital: float,
        risk_pct: Optional[float] = None,
        market_liquidity: Optional[float] = None,
    ) -> float:
        """
        Calculate appropriate position size

        Args:
            capital: Available capital
            risk_pct: Risk percentage (optional, uses default if not provided)
            market_liquidity: Market liquidity (optional, used to cap size)

        Returns:
            Position size in USD
        """
        if risk_pct is None:
            risk_pct = self.default_position_pct

        # Cap at max position percentage
        risk_pct = min(risk_pct, self.max_position_pct)

        # Calculate base position size
        position_size = capital * risk_pct

        # Cap at max position size
        position_size = min(position_size, self.max_position_size)

        # Cap based on market liquidity if provided
        if market_liquidity:
            # Don't use more than 10% of market liquidity
            max_liquid_size = market_liquidity * 0.1
            position_size = min(position_size, max_liquid_size)

        return position_size

    def check_can_trade(self, position_size: float) -> Tuple[bool, Optional[str]]:
        """
        Check if a trade can be executed based on risk limits

        Args:
            position_size: Proposed position size

        Returns:
            Tuple of (can_trade, reason_if_not)
        """
        # Reset daily limits if needed
        self.reset_daily_limits()

        # Check daily loss limit
        if self.daily_loss >= self.max_daily_loss:
            return (
                False,
                f"Daily loss limit reached (${self.daily_loss:.2f} >= ${self.max_daily_loss:.2f})",
            )

        # Check position size limit
        if position_size > self.max_position_size:
            return (
                False,
                f"Position size ${position_size:.2f} exceeds limit ${self.max_position_size:.2f}",
            )

        # Check total exposure
        total_exposure = sum(pos["size"] for pos in self.open_positions.values())

        if total_exposure + position_size > self.max_total_exposure:
            return (
                False,
                f"Total exposure would exceed limit (${total_exposure + position_size:.2f} > ${self.max_total_exposure:.2f})",
            )

        # Check max positions
        if len(self.open_positions) >= self.max_positions:
            return False, f"Maximum number of positions reached ({self.max_positions})"

        return True, None

    def record_trade(
        self,
        market_id: str,
        direction: str,
        size: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Record a new trade and set up risk management

        Args:
            market_id: Market identifier
            direction: Trade direction (long/short, buy/sell)
            size: Position size
            entry_price: Entry price
            stop_loss: Stop-loss price (optional)
            take_profit: Take-profit price (optional)

        Returns:
            Position dictionary
        """
        # Calculate default stop-loss and take-profit if not provided
        if stop_loss is None:
            if direction.lower() in ["long", "buy"]:
                stop_loss = entry_price * (1 - self.default_stop_loss_pct)
            else:
                stop_loss = entry_price * (1 + self.default_stop_loss_pct)

        if take_profit is None:
            if direction.lower() in ["long", "buy"]:
                take_profit = entry_price * (1 + self.default_take_profit_pct)
            else:
                take_profit = entry_price * (1 - self.default_take_profit_pct)

        position = {
            "market_id": market_id,
            "direction": direction,
            "size": size,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "entry_time": datetime.now().isoformat(),
            "unrealized_pnl": 0.0,
        }

        self.open_positions[market_id] = position
        self.daily_trades += 1

        logger.info(
            f"Recorded trade: {market_id} {direction} ${size:.2f} @ {entry_price:.4f}"
        )

        return position

    def record_pnl(self, pnl: float):
        """
        Record P&L from closed trade

        Args:
            pnl: Profit/Loss amount
        """
        if pnl < 0:
            self.daily_loss += abs(pnl)
            logger.info(
                f"Recorded loss: ${abs(pnl):.2f}, daily loss: ${self.daily_loss:.2f}"
            )

    def check_stop_loss_take_profit(
        self, market_id: str, current_price: float
    ) -> Optional[str]:
        """
        Check if stop-loss or take-profit should be triggered

        Args:
            market_id: Market identifier
            current_price: Current market price

        Returns:
            Action to take ("stop_loss", "take_profit") or None
        """
        if market_id not in self.open_positions:
            return None

        position = self.open_positions[market_id]
        direction = position["direction"].lower()
        stop_loss = position["stop_loss"]
        take_profit = position["take_profit"]

        # Check for long positions
        if direction in ["long", "buy"]:
            if current_price <= stop_loss:
                logger.warning(
                    f"Stop-loss triggered for {market_id}: {current_price:.4f} <= {stop_loss:.4f}"
                )
                return "stop_loss"

            if current_price >= take_profit:
                logger.info(
                    f"Take-profit triggered for {market_id}: {current_price:.4f} >= {take_profit:.4f}"
                )
                return "take_profit"

        # Check for short positions
        else:
            if current_price >= stop_loss:
                logger.warning(
                    f"Stop-loss triggered for {market_id}: {current_price:.4f} >= {stop_loss:.4f}"
                )
                return "stop_loss"

            if current_price <= take_profit:
                logger.info(
                    f"Take-profit triggered for {market_id}: {current_price:.4f} <= {take_profit:.4f}"
                )
                return "take_profit"

        return None

    def update_position_pnl(self, market_id: str, current_price: float):
        """
        Update unrealized P&L for a position

        Args:
            market_id: Market identifier
            current_price: Current market price
        """
        if market_id not in self.open_positions:
            return

        position = self.open_positions[market_id]
        entry_price = position["entry_price"]
        size = position["size"]
        direction = position["direction"].lower()

        # Calculate unrealized P&L
        if direction in ["long", "buy"]:
            pnl = (current_price - entry_price) * size
        else:
            pnl = (entry_price - current_price) * size

        position["unrealized_pnl"] = pnl

    def close_position(
        self, market_id: str, exit_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Close a position and calculate final P&L

        Args:
            market_id: Market identifier
            exit_price: Exit price

        Returns:
            Closed position with final P&L or None if not found
        """
        if market_id not in self.open_positions:
            return None

        position = self.open_positions.pop(market_id)

        # Calculate final P&L
        entry_price = position["entry_price"]
        size = position["size"]
        direction = position["direction"].lower()

        if direction in ["long", "buy"]:
            pnl = (exit_price - entry_price) * size
        else:
            pnl = (entry_price - exit_price) * size

        position["exit_price"] = exit_price
        position["exit_time"] = datetime.now().isoformat()
        position["realized_pnl"] = pnl

        # Record P&L
        self.record_pnl(pnl)

        logger.info(f"Closed position {market_id}: P&L ${pnl:.2f}")

        return position

    def get_position(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Get position details

        Args:
            market_id: Market identifier

        Returns:
            Position dictionary or None if not found
        """
        return self.open_positions.get(market_id)

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions

        Returns:
            List of position dictionaries
        """
        return list(self.open_positions.values())

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get current risk status summary

        Returns:
            Dictionary with risk metrics
        """
        self.reset_daily_limits()

        total_exposure = sum(pos["size"] for pos in self.open_positions.values())
        total_unrealized_pnl = sum(
            pos.get("unrealized_pnl", 0) for pos in self.open_positions.values()
        )

        return {
            "daily_loss": self.daily_loss,
            "daily_loss_limit": self.max_daily_loss,
            "daily_loss_remaining": max(0, self.max_daily_loss - self.daily_loss),
            "daily_trades": self.daily_trades,
            "open_positions": len(self.open_positions),
            "max_positions": self.max_positions,
            "total_exposure": total_exposure,
            "max_exposure": self.max_total_exposure,
            "exposure_remaining": max(0, self.max_total_exposure - total_exposure),
            "total_unrealized_pnl": total_unrealized_pnl,
            "can_trade": self.daily_loss < self.max_daily_loss
            and len(self.open_positions) < self.max_positions,
        }

    def check_all_positions(self, prices: Dict[str, float]) -> List[Tuple[str, str]]:
        """
        Check all positions for stop-loss or take-profit triggers

        Args:
            prices: Dictionary of market_id -> current price

        Returns:
            List of (market_id, action) tuples for positions to close
        """
        actions = []

        for market_id, position in self.open_positions.items():
            if market_id in prices:
                current_price = prices[market_id]

                # Update unrealized P&L
                self.update_position_pnl(market_id, current_price)

                # Check for triggers
                action = self.check_stop_loss_take_profit(market_id, current_price)

                if action:
                    actions.append((market_id, action))

        return actions


# Global instance
risk_manager: Optional[RiskManager] = None


def get_risk_manager(config: Optional[Dict[str, Any]] = None) -> RiskManager:
    """
    Get or create global risk manager instance

    Args:
        config: Configuration dictionary (required for first call)

    Returns:
        RiskManager instance
    """
    global risk_manager

    if risk_manager is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        risk_manager = RiskManager(config)

    return risk_manager
