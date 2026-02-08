"""
Paper Trading Engine - Unified Simulation System

Simulates real trading with live market data without risking real money.
Provides realistic execution simulation with:
- Order book depth simulation
- Slippage and market impact
- Commission and fees
- Portfolio tracking
- Performance analytics
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path

from logger import get_logger


class OrderType(Enum):
    """Order types"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides"""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order statuses"""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """Represents a trading order"""

    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.filled_quantity = 0.0
        self.avg_fill_price = 0.0
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.filled_at: Optional[datetime] = None
        self.commission = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "filled_quantity": self.filled_quantity,
            "avg_fill_price": self.avg_fill_price,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "commission": self.commission,
        }


class Position:
    """Represents a trading position"""

    def __init__(self, symbol: str, quantity: float, avg_price: float):
        self.symbol = symbol
        self.quantity = quantity
        self.avg_price = avg_price
        self.realized_pnl = 0.0
        self.opened_at = datetime.now()

    def update(self, quantity_change: float, price: float) -> float:
        """
        Update position with new trade

        Returns:
            Realized P&L from this update
        """
        realized_pnl = 0.0

        if quantity_change * self.quantity < 0:  # Closing position
            close_quantity = min(abs(quantity_change), abs(self.quantity))
            realized_pnl = (
                close_quantity
                * (price - self.avg_price)
                * (1 if self.quantity > 0 else -1)
            )
            self.realized_pnl += realized_pnl

        # Update position
        if abs(self.quantity + quantity_change) < 0.0001:  # Position closed
            self.quantity = 0
            self.avg_price = 0
        else:
            total_cost = self.quantity * self.avg_price + quantity_change * price
            self.quantity += quantity_change
            if self.quantity != 0:
                self.avg_price = total_cost / self.quantity

        return realized_pnl

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        return self.quantity * (current_price - self.avg_price)

    def to_dict(self, current_price: float = None) -> Dict[str, Any]:
        """Convert position to dictionary"""
        data = {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "realized_pnl": self.realized_pnl,
            "opened_at": self.opened_at.isoformat(),
        }
        if current_price:
            data["unrealized_pnl"] = self.unrealized_pnl(current_price)
            data["current_value"] = self.quantity * current_price
        return data


class PaperTradingEngine:
    """
    Paper trading engine for realistic trade simulation

    Features:
    - Multiple order types (market, limit, stop)
    - Realistic execution with slippage
    - Commission simulation
    - Portfolio tracking
    - Risk management
    - Performance analytics
    """

    def __init__(
        self,
        initial_balance: float = 10000.0,
        commission_rate: float = 0.001,  # 0.1%
        slippage_rate: float = 0.001,  # 0.1%
        log_dir: str = "logs",
        logger=None,
    ):
        """
        Initialize paper trading engine

        Args:
            initial_balance: Starting cash balance
            commission_rate: Commission rate as decimal (0.001 = 0.1%)
            slippage_rate: Average slippage as decimal
            log_dir: Directory for trade logs
            logger: Logger instance
        """
        self.logger = logger or get_logger()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Account state
        self.initial_balance = initial_balance
        self.cash_balance = initial_balance
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

        # Trading state
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0

        # Performance tracking
        self.trade_history: List[Dict[str, Any]] = []
        self.total_commission_paid = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0.0
        self.peak_balance = initial_balance

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Place a trading order

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop', 'stop_limit'
            quantity: Order quantity
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Order result dictionary
        """
        # Generate order ID
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:06d}"

        # Create order
        try:
            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=OrderSide(side.lower()),
                order_type=OrderType(order_type.lower()),
                quantity=quantity,
                price=price,
                stop_price=stop_price,
            )
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid order parameters: {str(e)}",
            }

        # Validate order
        validation = self._validate_order(order)
        if not validation["valid"]:
            order.status = OrderStatus.REJECTED
            return {
                "success": False,
                "order_id": order_id,
                "error": validation["reason"],
            }

        # Store order
        self.orders[order_id] = order

        # For market orders, execute immediately
        if order.order_type == OrderType.MARKET:
            # Need current price to execute
            return {
                "success": True,
                "order_id": order_id,
                "status": "pending_price",
                "message": "Market order created, call execute_order with current price",
            }

        return {
            "success": True,
            "order_id": order_id,
            "status": order.status.value,
            "order": order.to_dict(),
        }

    def execute_order(self, order_id: str, current_price: float) -> Dict[str, Any]:
        """
        Execute a pending order at current market price

        Args:
            order_id: Order ID to execute
            current_price: Current market price

        Returns:
            Execution result
        """
        if order_id not in self.orders:
            return {
                "success": False,
                "error": "Order not found",
            }

        order = self.orders[order_id]

        if order.status != OrderStatus.PENDING:
            return {
                "success": False,
                "error": f"Order already {order.status.value}",
            }

        # Check if order should be filled based on type
        should_fill, fill_price = self._check_fill_condition(order, current_price)

        if not should_fill:
            return {
                "success": False,
                "order_id": order_id,
                "reason": "price_condition_not_met",
            }

        # Simulate execution with slippage
        execution_price = self._apply_slippage(fill_price, order.side)

        # Calculate commission
        trade_value = order.quantity * execution_price
        commission = trade_value * self.commission_rate

        # Check if we have enough cash for buy orders
        if order.side == OrderSide.BUY:
            total_cost = trade_value + commission
            if total_cost > self.cash_balance:
                order.status = OrderStatus.REJECTED
                return {
                    "success": False,
                    "error": "Insufficient funds",
                    "required": total_cost,
                    "available": self.cash_balance,
                }

        # Execute the trade
        order.filled_quantity = order.quantity
        order.avg_fill_price = execution_price
        order.commission = commission
        order.status = OrderStatus.FILLED
        order.filled_at = datetime.now()

        # Update cash balance
        if order.side == OrderSide.BUY:
            self.cash_balance -= trade_value + commission
        else:
            self.cash_balance += trade_value - commission

        # Update position
        quantity_change = (
            order.quantity if order.side == OrderSide.BUY else -order.quantity
        )
        realized_pnl = self._update_position(
            order.symbol, quantity_change, execution_price
        )

        # Update metrics
        self.total_commission_paid += commission
        self.total_trades += 1

        if realized_pnl != 0:
            if realized_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1

        # Update drawdown
        self._update_drawdown()

        # Record trade
        trade_record = {
            "order_id": order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": execution_price,
            "commission": commission,
            "realized_pnl": realized_pnl,
            "timestamp": datetime.now().isoformat(),
        }
        self.trade_history.append(trade_record)

        # Log trade
        if self.logger:
            self.logger.log_trade(
                market=order.symbol,
                yes_price=execution_price,
                no_price=0,
                profit_usd=realized_pnl,
                status="filled",
                strategy="paper_trading",
                arbitrage_type=order.side.value,
            )

        return {
            "success": True,
            "order_id": order_id,
            "execution_price": execution_price,
            "commission": commission,
            "realized_pnl": realized_pnl,
            "cash_balance": self.cash_balance,
            "order": order.to_dict(),
        }

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a symbol"""
        if symbol not in self.positions or self.positions[symbol].quantity == 0:
            return None
        return self.positions[symbol].to_dict()

    def get_all_positions(
        self, current_prices: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """Get all open positions"""
        positions = []
        for symbol, position in self.positions.items():
            if position.quantity != 0:
                current_price = current_prices.get(symbol) if current_prices else None
                positions.append(position.to_dict(current_price))
        return positions

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        position_value = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.avg_price)
            for pos in self.positions.values()
            if pos.quantity != 0
        )
        return self.cash_balance + position_value

    def get_performance_metrics(
        self, current_prices: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        current_prices = current_prices or {}
        portfolio_value = self.get_portfolio_value(current_prices)

        total_return = portfolio_value - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100

        win_rate = (
            (self.winning_trades / (self.winning_trades + self.losing_trades) * 100)
            if (self.winning_trades + self.losing_trades) > 0
            else 0
        )

        return {
            "initial_balance": self.initial_balance,
            "cash_balance": self.cash_balance,
            "portfolio_value": portfolio_value,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate_pct": win_rate,
            "total_commission": self.total_commission_paid,
            "max_drawdown_pct": self.max_drawdown,
            "open_positions": len(
                [p for p in self.positions.values() if p.quantity != 0]
            ),
        }

    # Private helper methods

    def _validate_order(self, order: Order) -> Dict[str, Any]:
        """Validate order parameters"""
        if order.quantity <= 0:
            return {"valid": False, "reason": "Invalid quantity"}

        if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if not order.price or order.price <= 0:
                return {"valid": False, "reason": "Invalid price"}

        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if not order.stop_price or order.stop_price <= 0:
                return {"valid": False, "reason": "Invalid stop price"}

        return {"valid": True}

    def _check_fill_condition(
        self, order: Order, current_price: float
    ) -> Tuple[bool, float]:
        """Check if order should be filled at current price"""
        if order.order_type == OrderType.MARKET:
            return True, current_price

        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and current_price <= order.price:
                return True, order.price
            if order.side == OrderSide.SELL and current_price >= order.price:
                return True, order.price
            return False, 0

        if order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY and current_price >= order.stop_price:
                return True, current_price
            if order.side == OrderSide.SELL and current_price <= order.stop_price:
                return True, current_price
            return False, 0

        return False, 0

    def _apply_slippage(self, price: float, side: OrderSide) -> float:
        """Apply slippage to execution price"""
        if side == OrderSide.BUY:
            return price * (1 + self.slippage_rate)
        else:
            return price * (1 - self.slippage_rate)

    def _update_position(
        self, symbol: str, quantity_change: float, price: float
    ) -> float:
        """Update or create position, returns realized P&L"""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, 0, 0)

        return self.positions[symbol].update(quantity_change, price)

    def _update_drawdown(self) -> None:
        """Update maximum drawdown"""
        current_value = self.cash_balance + sum(
            pos.quantity * pos.avg_price
            for pos in self.positions.values()
            if pos.quantity != 0
        )

        if current_value > self.peak_balance:
            self.peak_balance = current_value

        if self.peak_balance > 0:
            drawdown = ((self.peak_balance - current_value) / self.peak_balance) * 100
            self.max_drawdown = max(self.max_drawdown, drawdown)
