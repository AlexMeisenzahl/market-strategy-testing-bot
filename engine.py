"""
Execution Engine - Single authoritative trade execution spine.

All trade execution flows through ExecutionEngine. It owns a PaperTradingEngine
internally and exposes execute_trade(signal) plus read-only state access.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from logger import get_logger
from services.paper_trading_engine import PaperTradingEngine


@dataclass
class TradeSignal:
    """Normalized trade intent; strategies produce these, engine executes."""

    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    order_type: str = "market"
    price: Optional[float] = None  # current price for market orders (needed for fill)
    strategy_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "price": self.price,
            "strategy_name": self.strategy_name,
        }


class ExecutionEngine:
    """Single execution engine. Uses PaperTradingEngine internally."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        initial_balance = config.get(
            "initial_capital", config.get("total_capital", 10000.0)
        )
        commission_rate = config.get("commission_rate", 0.001)
        slippage_rate = config.get("slippage_rate", 0.001)
        log_dir = config.get("log_dir", "logs")
        self._logger = get_logger()
        self.trading_engine = PaperTradingEngine(
            initial_balance=float(initial_balance),
            commission_rate=float(commission_rate),
            slippage_rate=float(slippage_rate),
            log_dir=log_dir,
            logger=self._logger,
        )

    def execute_trade(self, signal: Any) -> Dict[str, Any]:
        """
        Execute a single trade from a signal (buy or sell).
        Buy and sell signals use the same path: place_order -> execute_order.
        Sell signals reduce/close positions, update realized PnL, append to trade history.
        """
        if isinstance(signal, TradeSignal):
            symbol = signal.symbol
            side = signal.side
            quantity = signal.quantity
            order_type = signal.order_type or "market"
            price = signal.price
        elif isinstance(signal, dict):
            symbol = signal.get("symbol") or signal.get("market_id")
            side = signal.get("side", "buy")
            quantity = signal.get("quantity") or signal.get("size", 0)
            order_type = signal.get("order_type", "market")
            price = signal.get("price")
            if not symbol:
                return {"success": False, "error": "signal missing symbol or market_id"}
        else:
            return {"success": False, "error": "signal must be TradeSignal or dict"}

        if not quantity or quantity <= 0:
            return {"success": False, "error": "invalid quantity"}

        result = self.trading_engine.place_order(
            symbol=str(symbol),
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        if not result.get("success"):
            return result

        order_id = result.get("order_id")
        if order_id and result.get("status") == "pending_price":
            if price is None:
                return {
                    "success": False,
                    "error": "market order requires price (current price) in signal",
                    "order_id": order_id,
                }
            return self.trading_engine.execute_order(order_id, float(price))
        return result

    def get_positions(
        self, current_prices: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Read-only: current positions from the internal engine."""
        return self.trading_engine.get_all_positions(current_prices or {})

    def get_balance(self) -> float:
        """Read-only: cash balance."""
        return self.trading_engine.cash_balance

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Read-only: executed trades."""
        return list(self.trading_engine.trade_history)
