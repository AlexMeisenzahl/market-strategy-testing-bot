"""
Trade Verification System

Verifies that trades were actually executed on exchanges as expected.
Detects partial fills, slippage, and execution failures.
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class VerificationStatus(Enum):
    """Trade verification status"""

    VERIFIED = "verified"
    PARTIAL_FILL = "partial_fill"
    FAILED = "failed"
    PENDING = "pending"
    SLIPPAGE_HIGH = "slippage_high"
    TIMEOUT = "timeout"


class TradeVerifier:
    """
    Trade verification system

    Verifies trade execution by:
    - Checking order status on exchange
    - Verifying fill price matches expected
    - Detecting partial fills
    - Calculating actual slippage
    """

    def __init__(self, max_slippage_pct: float = 1.0):
        """
        Initialize trade verifier

        Args:
            max_slippage_pct: Maximum acceptable slippage percentage
        """
        self.logger = logging.getLogger(__name__)
        self.max_slippage_pct = max_slippage_pct
        self.verification_history = []

        self.logger.info("Trade Verifier initialized")
        self.logger.info(f"  Max acceptable slippage: {max_slippage_pct}%")

    def verify_trade(
        self,
        order_id: str,
        exchange: str,
        expected_price: float = None,
        expected_size: float = None,
    ) -> Dict:
        """
        Verify trade execution

        Args:
            order_id: Exchange order ID
            exchange: Exchange name ('binance', 'polymarket', etc.)
            expected_price: Expected execution price
            expected_size: Expected order size

        Returns:
            Dict with verification results:
            {
                'verified': bool,
                'status': VerificationStatus,
                'order_id': str,
                'exchange': str,
                'fill_status': str,
                'filled_size': float,
                'expected_size': float,
                'fill_price': float,
                'expected_price': float,
                'slippage_pct': float,
                'discrepancies': List[str],
                'timestamp': str
            }
        """
        self.logger.info(f"Verifying trade {order_id} on {exchange}...")

        try:
            # Get order details from exchange
            order_details = self._fetch_order_details(order_id, exchange)

            if not order_details:
                return self._create_verification_result(
                    verified=False,
                    status=VerificationStatus.FAILED,
                    order_id=order_id,
                    exchange=exchange,
                    error="Failed to fetch order details",
                )

            # Extract order info
            fill_status = order_details.get("status", "UNKNOWN")
            filled_size = order_details.get("filled_size", 0.0)
            fill_price = order_details.get("fill_price", 0.0)

            # Check if order is filled
            verified = fill_status in ["FILLED", "COMPLETED"]

            # Detect partial fills
            if expected_size and filled_size < expected_size * 0.99:
                status = VerificationStatus.PARTIAL_FILL
                verified = False
            elif not verified:
                status = (
                    VerificationStatus.PENDING
                    if fill_status == "PENDING"
                    else VerificationStatus.FAILED
                )
            else:
                status = VerificationStatus.VERIFIED

            # Calculate slippage
            slippage_pct = 0.0
            if expected_price and fill_price:
                slippage_pct = abs((fill_price - expected_price) / expected_price) * 100

                # Check if slippage exceeds threshold
                if slippage_pct > self.max_slippage_pct:
                    status = VerificationStatus.SLIPPAGE_HIGH
                    verified = False

            # Identify discrepancies
            discrepancies = []

            if (
                expected_size
                and abs(filled_size - expected_size) > expected_size * 0.01
            ):
                discrepancies.append(
                    f"Size mismatch: expected {expected_size}, got {filled_size}"
                )

            if slippage_pct > self.max_slippage_pct:
                discrepancies.append(
                    f"High slippage: {slippage_pct:.2f}% (max: {self.max_slippage_pct}%)"
                )

            if fill_status not in ["FILLED", "COMPLETED"]:
                discrepancies.append(f"Order status: {fill_status}")

            # Create verification result
            result = self._create_verification_result(
                verified=verified,
                status=status,
                order_id=order_id,
                exchange=exchange,
                fill_status=fill_status,
                filled_size=filled_size,
                expected_size=expected_size,
                fill_price=fill_price,
                expected_price=expected_price,
                slippage_pct=slippage_pct,
                discrepancies=discrepancies,
            )

            # Log result
            if verified:
                self.logger.info(
                    f"✓ Trade verified: {order_id} - "
                    f"Filled {filled_size} @ {fill_price} "
                    f"(slippage: {slippage_pct:.2f}%)"
                )
            else:
                self.logger.warning(
                    f"⚠ Trade verification failed: {order_id} - "
                    f"Status: {status.value}, Discrepancies: {len(discrepancies)}"
                )

            # Save to history
            self.verification_history.append(result)

            return result

        except Exception as e:
            self.logger.error(f"Error verifying trade {order_id}: {e}")
            return self._create_verification_result(
                verified=False,
                status=VerificationStatus.FAILED,
                order_id=order_id,
                exchange=exchange,
                error=str(e),
            )

    def _fetch_order_details(self, order_id: str, exchange: str) -> Optional[Dict]:
        """
        Fetch order details from exchange

        Args:
            order_id: Order ID
            exchange: Exchange name

        Returns:
            Dict with order details or None

        Note: This is a placeholder - in production, this would call
        actual exchange APIs
        """
        # Placeholder - simulated order details
        # In production, this would call exchange-specific APIs:
        # - Binance: client.get_order()
        # - Polymarket: query subgraph or API
        # - etc.

        # Simulate successful trade
        simulated_order = {
            "order_id": order_id,
            "exchange": exchange,
            "status": "FILLED",
            "filled_size": 100.0,
            "fill_price": 50000.0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return simulated_order

    def _create_verification_result(
        self,
        verified: bool,
        status: VerificationStatus,
        order_id: str,
        exchange: str,
        fill_status: str = None,
        filled_size: float = None,
        expected_size: float = None,
        fill_price: float = None,
        expected_price: float = None,
        slippage_pct: float = None,
        discrepancies: list = None,
        error: str = None,
    ) -> Dict:
        """Create standardized verification result"""
        return {
            "verified": verified,
            "status": status.value,
            "order_id": order_id,
            "exchange": exchange,
            "fill_status": fill_status,
            "filled_size": filled_size,
            "expected_size": expected_size,
            "fill_price": fill_price,
            "expected_price": expected_price,
            "slippage_pct": slippage_pct,
            "discrepancies": discrepancies or [],
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def verify_multiple_trades(self, orders: list) -> Dict:
        """
        Verify multiple trades

        Args:
            orders: List of order dicts with 'order_id', 'exchange', etc.

        Returns:
            Dict with batch verification results
        """
        self.logger.info(f"Verifying {len(orders)} trades...")

        results = []
        verified_count = 0

        for order in orders:
            result = self.verify_trade(
                order_id=order["order_id"],
                exchange=order["exchange"],
                expected_price=order.get("expected_price"),
                expected_size=order.get("expected_size"),
            )
            results.append(result)

            if result["verified"]:
                verified_count += 1

        self.logger.info(
            f"✓ Batch verification complete: {verified_count}/{len(orders)} verified"
        )

        return {
            "success": True,
            "total_orders": len(orders),
            "verified_count": verified_count,
            "failed_count": len(orders) - verified_count,
            "results": results,
        }

    def get_verification_statistics(self) -> Dict:
        """
        Get verification statistics

        Returns:
            Dict with verification stats
        """
        if not self.verification_history:
            return {
                "total_verifications": 0,
                "verified_count": 0,
                "failed_count": 0,
                "partial_fills": 0,
                "high_slippage_count": 0,
                "avg_slippage_pct": 0.0,
            }

        verified_count = sum(1 for v in self.verification_history if v["verified"])
        failed_count = len(self.verification_history) - verified_count
        partial_fills = sum(
            1
            for v in self.verification_history
            if v["status"] == VerificationStatus.PARTIAL_FILL.value
        )
        high_slippage = sum(
            1
            for v in self.verification_history
            if v["status"] == VerificationStatus.SLIPPAGE_HIGH.value
        )

        slippages = [
            v["slippage_pct"]
            for v in self.verification_history
            if v["slippage_pct"] is not None
        ]
        avg_slippage = sum(slippages) / len(slippages) if slippages else 0.0

        return {
            "total_verifications": len(self.verification_history),
            "verified_count": verified_count,
            "failed_count": failed_count,
            "partial_fills": partial_fills,
            "high_slippage_count": high_slippage,
            "avg_slippage_pct": avg_slippage,
            "verification_rate": (verified_count / len(self.verification_history))
            * 100,
            "recent_verifications": self.verification_history[-10:],
        }

    def get_discrepancy_report(self) -> Dict:
        """
        Get report of all discrepancies found

        Returns:
            Dict with discrepancy report
        """
        discrepancies = []

        for verification in self.verification_history:
            if verification["discrepancies"]:
                discrepancies.append(
                    {
                        "order_id": verification["order_id"],
                        "exchange": verification["exchange"],
                        "timestamp": verification["timestamp"],
                        "discrepancies": verification["discrepancies"],
                    }
                )

        return {
            "total_discrepancies": len(discrepancies),
            "discrepancies": discrepancies,
        }


# Global instance
trade_verifier = TradeVerifier()
