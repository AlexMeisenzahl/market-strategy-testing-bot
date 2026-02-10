"""
Portfolio Tracker - Real-Time Portfolio Management

Tracks positions, balances, and performance metrics in real-time.
"""

from typing import Dict, List, Any
from datetime import datetime, timezone
from pathlib import Path
import json

from logger import get_logger


class PortfolioTracker:
    """Manages portfolio state and tracking"""

    def __init__(self, initial_balance: float = 10000.0):
        """
        Initialize portfolio tracker

        Args:
            initial_balance: Starting cash balance
        """
        self.logger = get_logger()
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {}  # symbol -> {quantity, avg_price, current_price}
        self.trades = []
        self.data_file = Path("data/portfolio_state.json")
        self.data_file.parent.mkdir(exist_ok=True)

        # Load existing state if available
        self._load_state()

    def _load_state(self):
        """Load portfolio state from disk"""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    state = json.load(f)
                    self.cash = state.get("cash", self.initial_balance)
                    self.positions = state.get("positions", {})
                    self.trades = state.get("trades", [])
                    self.logger.log_info(
                        f"Loaded portfolio state: ${self.cash:.2f} cash"
                    )
        except Exception as e:
            self.logger.log_error(f"Failed to load portfolio state: {e}")

    def _save_state(self):
        """Save portfolio state to disk"""
        try:
            state = {
                "cash": self.cash,
                "positions": self.positions,
                "trades": self.trades[-1000:],  # Keep last 1000 trades
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            with open(self.data_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.log_error(f"Failed to save portfolio state: {e}")

    def update(self, trade: Dict[str, Any]):
        """
        Update portfolio based on trade execution

        Args:
            trade: Trade dictionary with symbol, side, quantity, price
        """
        symbol = trade.get("symbol", "")
        side = trade.get("side", "").upper()
        quantity = trade.get("quantity", 0)
        price = trade.get("price", 0)

        if side == "BUY":
            # Deduct cash
            cost = quantity * price
            self.cash -= cost

            # Add/update position
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_quantity = pos["quantity"] + quantity
                total_cost = (pos["quantity"] * pos["avg_price"]) + cost
                pos["quantity"] = total_quantity
                pos["avg_price"] = total_cost / total_quantity
            else:
                self.positions[symbol] = {
                    "quantity": quantity,
                    "avg_price": price,
                    "current_price": price,
                }

        elif side == "SELL":
            # Add cash
            proceeds = quantity * price
            self.cash += proceeds

            # Remove/update position
            if symbol in self.positions:
                pos = self.positions[symbol]
                pos["quantity"] -= quantity
                if pos["quantity"] <= 0:
                    del self.positions[symbol]

        # Record trade
        self.trades.append(
            {**trade, "timestamp": datetime.now(timezone.utc).isoformat()}
        )

        # Save state
        self._save_state()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary

        Returns:
            Dictionary with portfolio metrics
        """
        total_value = self.cash
        for symbol, pos in self.positions.items():
            total_value += pos["quantity"] * pos.get("current_price", pos["avg_price"])

        return {
            "cash": self.cash,
            "total_value": total_value,
            "initial_balance": self.initial_balance,
            "total_return": total_value - self.initial_balance,
            "total_return_pct": ((total_value / self.initial_balance) - 1) * 100,
            "positions_count": len(self.positions),
            "trades_count": len(self.trades),
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all current positions

        Returns:
            List of position dictionaries
        """
        positions = []
        for symbol, pos in self.positions.items():
            current_price = pos.get("current_price", pos["avg_price"])
            value = pos["quantity"] * current_price
            positions.append(
                {
                    "symbol": symbol,
                    "quantity": pos["quantity"],
                    "avg_price": pos["avg_price"],
                    "current_price": current_price,
                    "value": value,
                    "pnl": value - (pos["quantity"] * pos["avg_price"]),
                    "pnl_pct": ((current_price / pos["avg_price"]) - 1) * 100,
                }
            )
        return positions

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for positions

        Args:
            prices: Dictionary mapping symbol to current price
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol]["current_price"] = price
        self._save_state()
