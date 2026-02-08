"""
Exit Manager

Manages stop-loss, take-profit, and time-based exits for open positions.
Monitors positions continuously and executes automatic exits when conditions are met.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from services.position_tracker import position_tracker, Position
from database.models import PositionConfig


class ExitManager:
    """
    Exit manager for stop-loss and take-profit automation

    Monitors all open positions and automatically exits when:
    - Stop-loss hit (default: -5%)
    - Take-profit hit (default: +10%)
    - Max hold time reached (default: 24 hours)
    - Trailing stop-loss hit
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_stop_loss_pct = -5.0
        self.default_take_profit_pct = 10.0
        self.default_max_hold_hours = 24
        self.exit_history = []

        self.logger.info("Exit Manager initialized")
        self.logger.info(f"  Default Stop-Loss: {self.default_stop_loss_pct}%")
        self.logger.info(f"  Default Take-Profit: {self.default_take_profit_pct}%")
        self.logger.info(f"  Default Max Hold: {self.default_max_hold_hours} hours")

    def check_exit_conditions(
        self, position: Position, current_price: float = None
    ) -> Optional[str]:
        """
        Check if position should be exited

        Args:
            position: Position to check
            current_price: Current market price (if None, uses position's current value)

        Returns:
            Exit reason string if should exit, None otherwise

        Examples:
            - "stop_loss_-5.2%"
            - "take_profit_+12.3%"
            - "max_hold_time_25hrs"
            - "trailing_stop_-3.1%"
        """
        # Get position config (or use defaults)
        config = PositionConfig.get_config(position.position_id)

        if config:
            stop_loss_pct = config["stop_loss_pct"]
            take_profit_pct = config["take_profit_pct"]
            max_hold_hours = config["max_hold_hours"]
            trailing_stop = config.get("trailing_stop")
        else:
            stop_loss_pct = self.default_stop_loss_pct
            take_profit_pct = self.default_take_profit_pct
            max_hold_hours = self.default_max_hold_hours
            trailing_stop = None

        # Calculate current profit percentage
        if current_price:
            current_value = position.size * (current_price / position.entry_price)
            profit = current_value - position.size
        else:
            profit = position.expected_profit

        profit_pct = (profit / position.size) * 100

        # Check stop-loss
        if profit_pct <= stop_loss_pct:
            reason = f"stop_loss_{profit_pct:.1f}%"
            self.logger.info(
                f"Position {position.position_id} hit stop-loss: {profit_pct:.1f}%"
            )
            return reason

        # Check take-profit
        if profit_pct >= take_profit_pct:
            reason = f"take_profit_+{profit_pct:.1f}%"
            self.logger.info(
                f"Position {position.position_id} hit take-profit: {profit_pct:.1f}%"
            )
            return reason

        # Check max hold time
        if position.entry_time:
            hold_time = datetime.utcnow() - position.entry_time
            hold_hours = hold_time.total_seconds() / 3600

            if hold_hours >= max_hold_hours:
                reason = f"max_hold_time_{int(hold_hours)}hrs"
                self.logger.info(
                    f"Position {position.position_id} reached max hold time: "
                    f"{hold_hours:.1f} hours"
                )
                return reason

        # Check trailing stop
        if trailing_stop and hasattr(position, "peak_profit_pct"):
            # If current profit is trailing_stop% below peak, exit
            drawdown_from_peak = position.peak_profit_pct - profit_pct

            if drawdown_from_peak >= trailing_stop:
                reason = f"trailing_stop_{profit_pct:.1f}%"
                self.logger.info(
                    f"Position {position.position_id} hit trailing stop: "
                    f"{drawdown_from_peak:.1f}% from peak"
                )
                return reason

        # No exit condition met
        return None

    def execute_exit(
        self, position: Position, reason: str, current_price: float = None
    ) -> Dict:
        """
        Execute position exit

        Args:
            position: Position to exit
            reason: Exit reason
            current_price: Current market price

        Returns:
            Dict with exit result
        """
        self.logger.info(
            f"Executing exit for position {position.position_id}: {reason}"
        )

        try:
            # Calculate exit values
            if current_price:
                exit_value = position.size * (current_price / position.entry_price)
            else:
                exit_value = position.size + position.expected_profit

            profit = exit_value - position.size
            profit_pct = (profit / position.size) * 100

            # Close position
            position_tracker.close_position(
                position.position_id, actual_profit=profit, exit_reason=reason
            )

            # Record exit
            exit_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "position_id": position.position_id,
                "strategy": position.strategy,
                "entry_price": position.entry_price,
                "exit_price": current_price,
                "profit": profit,
                "profit_pct": profit_pct,
                "reason": reason,
                "hold_time_hours": (
                    (datetime.utcnow() - position.entry_time).total_seconds() / 3600
                    if position.entry_time
                    else 0
                ),
            }
            self.exit_history.append(exit_record)

            self.logger.info(
                f"✓ Position closed: {profit_pct:+.1f}% profit, Reason: {reason}"
            )

            return {
                "success": True,
                "position_id": position.position_id,
                "profit": profit,
                "profit_pct": profit_pct,
                "reason": reason,
            }

        except Exception as e:
            self.logger.error(f"Failed to execute exit: {e}")
            return {
                "success": False,
                "position_id": position.position_id,
                "error": str(e),
            }

    def monitor_all_positions(
        self, current_prices: Dict[str, float] = None
    ) -> List[Dict]:
        """
        Monitor all open positions and execute exits as needed

        Args:
            current_prices: Dict of symbol -> current price

        Returns:
            List of exit results
        """
        open_positions = position_tracker.get_open_positions()

        if not open_positions:
            return []

        self.logger.info(f"Monitoring {len(open_positions)} open positions...")

        exits = []
        for position in open_positions:
            # Get current price for this position's symbol
            current_price = None
            if current_prices and position.symbol in current_prices:
                current_price = current_prices[position.symbol]

            # Check exit conditions
            exit_reason = self.check_exit_conditions(position, current_price)

            if exit_reason:
                # Execute exit
                result = self.execute_exit(position, exit_reason, current_price)
                exits.append(result)

        if exits:
            self.logger.info(f"✓ Executed {len(exits)} exits")

        return exits

    def set_position_config(
        self,
        position_id: str,
        stop_loss_pct: float = None,
        take_profit_pct: float = None,
        max_hold_hours: int = None,
        trailing_stop: float = None,
    ):
        """
        Set custom exit configuration for a position

        Args:
            position_id: Position ID
            stop_loss_pct: Stop-loss percentage (negative value)
            take_profit_pct: Take-profit percentage (positive value)
            max_hold_hours: Maximum hold time in hours
            trailing_stop: Trailing stop percentage
        """
        # Get existing config or use defaults
        existing_config = PositionConfig.get_config(position_id) or {
            "stop_loss_pct": self.default_stop_loss_pct,
            "take_profit_pct": self.default_take_profit_pct,
            "max_hold_hours": self.default_max_hold_hours,
            "trailing_stop": None,
        }

        # Update with new values
        if stop_loss_pct is not None:
            existing_config["stop_loss_pct"] = stop_loss_pct
        if take_profit_pct is not None:
            existing_config["take_profit_pct"] = take_profit_pct
        if max_hold_hours is not None:
            existing_config["max_hold_hours"] = max_hold_hours
        if trailing_stop is not None:
            existing_config["trailing_stop"] = trailing_stop

        # Save to database
        PositionConfig.set_config(
            position_id=position_id,
            stop_loss_pct=existing_config["stop_loss_pct"],
            take_profit_pct=existing_config["take_profit_pct"],
            max_hold_hours=existing_config["max_hold_hours"],
            trailing_stop=existing_config["trailing_stop"],
        )

        self.logger.info(f"Position config updated for {position_id}")

    def get_exit_statistics(self) -> Dict:
        """
        Get statistics about exits

        Returns:
            Dict with exit statistics
        """
        if not self.exit_history:
            return {
                "total_exits": 0,
                "stop_loss_exits": 0,
                "take_profit_exits": 0,
                "time_based_exits": 0,
                "trailing_stop_exits": 0,
                "avg_profit_pct": 0.0,
            }

        stop_loss_exits = sum(
            1 for e in self.exit_history if "stop_loss" in e["reason"]
        )
        take_profit_exits = sum(
            1 for e in self.exit_history if "take_profit" in e["reason"]
        )
        time_based_exits = sum(
            1 for e in self.exit_history if "max_hold" in e["reason"]
        )
        trailing_stop_exits = sum(
            1 for e in self.exit_history if "trailing_stop" in e["reason"]
        )

        avg_profit_pct = sum(e["profit_pct"] for e in self.exit_history) / len(
            self.exit_history
        )

        return {
            "total_exits": len(self.exit_history),
            "stop_loss_exits": stop_loss_exits,
            "take_profit_exits": take_profit_exits,
            "time_based_exits": time_based_exits,
            "trailing_stop_exits": trailing_stop_exits,
            "avg_profit_pct": avg_profit_pct,
            "recent_exits": self.exit_history[-10:],  # Last 10 exits
        }

    def update_defaults(
        self,
        stop_loss_pct: float = None,
        take_profit_pct: float = None,
        max_hold_hours: int = None,
    ):
        """
        Update default exit parameters

        Args:
            stop_loss_pct: New default stop-loss percentage
            take_profit_pct: New default take-profit percentage
            max_hold_hours: New default max hold time
        """
        if stop_loss_pct is not None:
            self.default_stop_loss_pct = stop_loss_pct
            self.logger.info(f"Default stop-loss updated to {stop_loss_pct}%")

        if take_profit_pct is not None:
            self.default_take_profit_pct = take_profit_pct
            self.logger.info(f"Default take-profit updated to {take_profit_pct}%")

        if max_hold_hours is not None:
            self.default_max_hold_hours = max_hold_hours
            self.logger.info(f"Default max hold updated to {max_hold_hours} hours")


# Global instance
exit_manager = ExitManager()
