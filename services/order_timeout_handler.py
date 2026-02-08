"""
Order Timeout Handler

Monitors orders for timeouts and automatically cancels orders
that don't fill within the specified timeout period.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum


class OrderStatus(Enum):
    """Order status"""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderTimeoutHandler:
    """
    Order timeout handler

    Monitors orders and:
    - Tracks order age
    - Cancels orders that exceed timeout
    - Reports timeout statistics
    """

    def __init__(self, default_timeout: int = 30):
        """
        Initialize order timeout handler

        Args:
            default_timeout: Default timeout in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.default_timeout = default_timeout
        self.monitored_orders = {}  # order_id -> order info
        self.timeout_history = []
        self.lock = threading.Lock()

        self.logger.info("Order Timeout Handler initialized")
        self.logger.info(f"  Default timeout: {default_timeout} seconds")

    def monitor_order(
        self, order_id: str, exchange: str, timeout_seconds: int = None
    ) -> bool:
        """
        Monitor an order for timeout

        This method blocks until order is filled or timeout is reached.

        Args:
            order_id: Order ID to monitor
            exchange: Exchange name
            timeout_seconds: Timeout in seconds (None = use default)

        Returns:
            True if order filled, False if timeout
        """
        if timeout_seconds is None:
            timeout_seconds = self.default_timeout

        self.logger.info(
            f"Monitoring order {order_id} on {exchange} "
            f"(timeout: {timeout_seconds}s)"
        )

        # Add to monitored orders
        with self.lock:
            self.monitored_orders[order_id] = {
                "order_id": order_id,
                "exchange": exchange,
                "start_time": time.time(),
                "timeout_seconds": timeout_seconds,
                "status": OrderStatus.PENDING,
            }

        # Poll order status until filled or timeout
        start_time = time.time()
        check_interval = min(
            5, timeout_seconds / 10
        )  # Check every 5s or 10% of timeout

        while True:
            elapsed = time.time() - start_time

            # Check if timeout reached
            if elapsed >= timeout_seconds:
                self.logger.warning(f"Order {order_id} timeout after {elapsed:.1f}s")
                return self._handle_timeout(order_id, exchange)

            # Check order status
            order_status = self._check_order_status(order_id, exchange)

            if order_status == OrderStatus.FILLED:
                self.logger.info(f"✓ Order {order_id} filled in {elapsed:.1f}s")
                self._mark_filled(order_id)
                return True

            elif order_status == OrderStatus.CANCELLED:
                self.logger.info(f"Order {order_id} was cancelled")
                self._mark_cancelled(order_id)
                return False

            elif order_status == OrderStatus.FAILED:
                self.logger.error(f"Order {order_id} failed")
                self._mark_failed(order_id)
                return False

            # Wait before next check
            time.sleep(check_interval)

    def monitor_order_async(
        self, order_id: str, exchange: str, timeout_seconds: int = None, callback=None
    ):
        """
        Monitor an order asynchronously (non-blocking)

        Args:
            order_id: Order ID to monitor
            exchange: Exchange name
            timeout_seconds: Timeout in seconds
            callback: Function to call when monitoring completes
                     callback(order_id, filled: bool)
        """

        def monitor_thread():
            filled = self.monitor_order(order_id, exchange, timeout_seconds)
            if callback:
                callback(order_id, filled)

        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()

        self.logger.info(f"Started async monitoring for order {order_id}")

    def _check_order_status(self, order_id: str, exchange: str) -> OrderStatus:
        """
        Check order status on exchange

        Args:
            order_id: Order ID
            exchange: Exchange name

        Returns:
            OrderStatus enum

        Note: This is a placeholder - in production, would query actual exchange
        """
        # Placeholder - in production, would call exchange API:
        # - Binance: client.get_order(orderId=order_id)
        # - Polymarket: query order status
        # etc.

        # Simulate order filling after 10 seconds (for testing)
        with self.lock:
            order_info = self.monitored_orders.get(order_id)
            if order_info:
                elapsed = time.time() - order_info["start_time"]
                # 70% chance of filling within 10 seconds
                if elapsed > 10 and elapsed % 1 < 0.1:
                    return OrderStatus.FILLED

        return OrderStatus.PENDING

    def _handle_timeout(self, order_id: str, exchange: str) -> bool:
        """
        Handle order timeout

        Args:
            order_id: Order ID
            exchange: Exchange name

        Returns:
            False (order not filled)
        """
        self.logger.warning(f"Cancelling timeout order: {order_id}")

        # Cancel order on exchange
        cancelled = self._cancel_order(order_id, exchange)

        # Update status
        with self.lock:
            if order_id in self.monitored_orders:
                order_info = self.monitored_orders[order_id]
                order_info["status"] = OrderStatus.TIMEOUT
                order_info["end_time"] = time.time()
                order_info["cancelled"] = cancelled

                # Add to history
                self.timeout_history.append(order_info.copy())

                # Remove from monitoring
                del self.monitored_orders[order_id]

        if cancelled:
            self.logger.info(f"✓ Order {order_id} cancelled due to timeout")
        else:
            self.logger.error(f"Failed to cancel timeout order: {order_id}")

        return False

    def _cancel_order(self, order_id: str, exchange: str) -> bool:
        """
        Cancel order on exchange

        Args:
            order_id: Order ID
            exchange: Exchange name

        Returns:
            True if cancelled successfully

        Note: This is a placeholder - in production, would call exchange API
        """
        # Placeholder - in production, would call:
        # - Binance: client.cancel_order(orderId=order_id)
        # - Polymarket: cancel order via API
        # etc.

        self.logger.info(f"Cancelling order {order_id} on {exchange}")

        # Simulate successful cancellation
        return True

    def _mark_filled(self, order_id: str):
        """Mark order as filled"""
        with self.lock:
            if order_id in self.monitored_orders:
                order_info = self.monitored_orders[order_id]
                order_info["status"] = OrderStatus.FILLED
                order_info["end_time"] = time.time()
                del self.monitored_orders[order_id]

    def _mark_cancelled(self, order_id: str):
        """Mark order as cancelled"""
        with self.lock:
            if order_id in self.monitored_orders:
                order_info = self.monitored_orders[order_id]
                order_info["status"] = OrderStatus.CANCELLED
                order_info["end_time"] = time.time()
                del self.monitored_orders[order_id]

    def _mark_failed(self, order_id: str):
        """Mark order as failed"""
        with self.lock:
            if order_id in self.monitored_orders:
                order_info = self.monitored_orders[order_id]
                order_info["status"] = OrderStatus.FAILED
                order_info["end_time"] = time.time()
                del self.monitored_orders[order_id]

    def get_monitored_orders(self) -> List[Dict]:
        """
        Get list of currently monitored orders

        Returns:
            List of order info dicts
        """
        with self.lock:
            return [
                {
                    "order_id": info["order_id"],
                    "exchange": info["exchange"],
                    "age_seconds": time.time() - info["start_time"],
                    "timeout_seconds": info["timeout_seconds"],
                    "status": info["status"].value,
                }
                for info in self.monitored_orders.values()
            ]

    def get_timeout_statistics(self) -> Dict:
        """
        Get timeout statistics

        Returns:
            Dict with timeout stats
        """
        if not self.timeout_history:
            return {
                "total_timeouts": 0,
                "cancelled_count": 0,
                "cancel_success_rate": 0.0,
                "avg_timeout_age": 0.0,
            }

        cancelled_count = sum(1 for t in self.timeout_history if t.get("cancelled"))
        ages = [
            t["end_time"] - t["start_time"]
            for t in self.timeout_history
            if "end_time" in t
        ]
        avg_age = sum(ages) / len(ages) if ages else 0.0

        return {
            "total_timeouts": len(self.timeout_history),
            "cancelled_count": cancelled_count,
            "cancel_success_rate": (cancelled_count / len(self.timeout_history)) * 100,
            "avg_timeout_age": avg_age,
            "recent_timeouts": self.timeout_history[-10:],
        }

    def set_default_timeout(self, timeout_seconds: int):
        """
        Set default timeout

        Args:
            timeout_seconds: New default timeout in seconds
        """
        self.default_timeout = timeout_seconds
        self.logger.info(f"Default timeout updated to {timeout_seconds}s")

    def cancel_all_monitored(self) -> Dict:
        """
        Cancel all currently monitored orders

        Returns:
            Dict with cancellation results
        """
        with self.lock:
            orders = list(self.monitored_orders.values())

        if not orders:
            return {"success": True, "cancelled_count": 0}

        self.logger.warning(f"Cancelling {len(orders)} monitored orders...")

        cancelled_count = 0
        for order_info in orders:
            cancelled = self._cancel_order(
                order_info["order_id"], order_info["exchange"]
            )
            if cancelled:
                cancelled_count += 1

        # Clear monitored orders
        with self.lock:
            self.monitored_orders.clear()

        self.logger.info(f"✓ Cancelled {cancelled_count}/{len(orders)} orders")

        return {
            "success": True,
            "total_orders": len(orders),
            "cancelled_count": cancelled_count,
        }


# Global instance
order_timeout_handler = OrderTimeoutHandler()
