"""
Arbitrage Executor Module

Executes different types of arbitrage opportunities with rollback on failure.
Supports 2-way, 3-way, and multi-leg arbitrage strategies.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
from strategies.arbitrage_types import ArbitrageOpportunity, ArbitrageType, ArbitrageLeg
from strategies.kalshi_priority import validate_kalshi_first
from strategies.rollback_handler import RollbackHandler

# Get logger for this module
logger = logging.getLogger(__name__)


class ArbitrageExecutor:
    """
    Executes arbitrage opportunities with type-specific logic

    Routes execution to appropriate method based on arbitrage type.
    Validates Kalshi-first rule before execution.
    Implements rollback on failure.
    """

    def __init__(self):
        """Initialize executor with rollback handler"""
        self.rollback_handler = RollbackHandler()

    def execute_two_way(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """
        Execute simple 2-leg arbitrage

        Executes both legs in order. If second leg fails, rolls back first leg.

        Args:
            opportunity: ArbitrageOpportunity with 2 legs

        Returns:
            Execution result dictionary
        """
        logger.info(
            f"Executing 2-way arbitrage (profit: ${opportunity.expected_profit:.2f})"
        )

        if len(opportunity.legs) != 2:
            return {
                "success": False,
                "type": ArbitrageType.TWO_WAY.value,
                "legs_executed": 0,
                "legs_failed": len(opportunity.legs),
                "profit": 0.0,
                "error": f"2-way arbitrage requires exactly 2 legs, got {len(opportunity.legs)}",
                "timestamp": datetime.now(),
            }

        executed_legs: List[ArbitrageLeg] = []

        # Sort legs by execution order
        sorted_legs = sorted(opportunity.legs, key=lambda leg: leg.order)

        # Execute first leg
        leg1 = sorted_legs[0]
        logger.info(f"Executing leg 1: {leg1.exchange} {leg1.action} {leg1.market_id}")

        # Simulate execution (in production, would call exchange API)
        leg1_success = self._execute_leg(leg1)

        if not leg1_success:
            logger.error(f"Leg 1 failed: {leg1.exchange} {leg1.market_id}")
            return {
                "success": False,
                "type": ArbitrageType.TWO_WAY.value,
                "legs_executed": 0,
                "legs_failed": 1,
                "profit": 0.0,
                "error": "First leg execution failed",
                "timestamp": datetime.now(),
            }

        executed_legs.append(leg1)
        logger.info(f"✓ Leg 1 executed successfully")

        # Execute second leg
        leg2 = sorted_legs[1]
        logger.info(f"Executing leg 2: {leg2.exchange} {leg2.action} {leg2.market_id}")

        leg2_success = self._execute_leg(leg2)

        if not leg2_success:
            logger.error(f"Leg 2 failed: {leg2.exchange} {leg2.market_id}")
            logger.warning("Rolling back leg 1...")

            # Rollback first leg
            self.rollback_handler.rollback_opportunity(executed_legs)

            return {
                "success": False,
                "type": ArbitrageType.TWO_WAY.value,
                "legs_executed": 1,
                "legs_failed": 1,
                "profit": 0.0,
                "error": "Second leg execution failed, rolled back first leg",
                "timestamp": datetime.now(),
            }

        executed_legs.append(leg2)
        logger.info(f"✓ Leg 2 executed successfully")

        # Both legs successful
        return {
            "success": True,
            "type": ArbitrageType.TWO_WAY.value,
            "legs_executed": 2,
            "legs_failed": 0,
            "profit": opportunity.expected_profit,
            "error": None,
            "timestamp": datetime.now(),
        }

    def execute_three_way(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """
        Execute 3-leg triangular arbitrage

        Executes all legs in order. Rolls back completed legs if any leg fails.

        Args:
            opportunity: ArbitrageOpportunity with 3 legs

        Returns:
            Execution result dictionary
        """
        logger.info(
            f"Executing 3-way arbitrage (profit: ${opportunity.expected_profit:.2f})"
        )

        if len(opportunity.legs) != 3:
            return {
                "success": False,
                "type": ArbitrageType.THREE_WAY.value,
                "legs_executed": 0,
                "legs_failed": len(opportunity.legs),
                "profit": 0.0,
                "error": f"3-way arbitrage requires exactly 3 legs, got {len(opportunity.legs)}",
                "timestamp": datetime.now(),
            }

        executed_legs: List[ArbitrageLeg] = []
        sorted_legs = sorted(opportunity.legs, key=lambda leg: leg.order)

        # Execute each leg sequentially
        for i, leg in enumerate(sorted_legs, start=1):
            logger.info(
                f"Executing leg {i}: {leg.exchange} {leg.action} {leg.market_id}"
            )

            success = self._execute_leg(leg)

            if not success:
                logger.error(f"Leg {i} failed: {leg.exchange} {leg.market_id}")

                # Rollback all executed legs
                if executed_legs:
                    logger.warning(
                        f"Rolling back {len(executed_legs)} executed legs..."
                    )
                    self.rollback_handler.rollback_opportunity(executed_legs)

                return {
                    "success": False,
                    "type": ArbitrageType.THREE_WAY.value,
                    "legs_executed": len(executed_legs),
                    "legs_failed": 3 - len(executed_legs),
                    "profit": 0.0,
                    "error": f"Leg {i} execution failed, rolled back {len(executed_legs)} legs",
                    "timestamp": datetime.now(),
                }

            executed_legs.append(leg)
            logger.info(f"✓ Leg {i} executed successfully")

        # All legs successful
        return {
            "success": True,
            "type": ArbitrageType.THREE_WAY.value,
            "legs_executed": 3,
            "legs_failed": 0,
            "profit": opportunity.expected_profit,
            "error": None,
            "timestamp": datetime.now(),
        }

    def execute_multi_leg(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """
        Execute complex multi-leg arbitrage (4+ legs)

        Executes all legs in order. Rolls back all completed legs on any failure.

        Args:
            opportunity: ArbitrageOpportunity with 4+ legs

        Returns:
            Execution result dictionary
        """
        num_legs = len(opportunity.legs)
        logger.info(
            f"Executing multi-leg arbitrage ({num_legs} legs, profit: ${opportunity.expected_profit:.2f})"
        )

        if num_legs < 4:
            return {
                "success": False,
                "type": ArbitrageType.MULTI_LEG.value,
                "legs_executed": 0,
                "legs_failed": num_legs,
                "profit": 0.0,
                "error": f"Multi-leg arbitrage requires 4+ legs, got {num_legs}",
                "timestamp": datetime.now(),
            }

        executed_legs: List[ArbitrageLeg] = []
        sorted_legs = sorted(opportunity.legs, key=lambda leg: leg.order)

        # Execute each leg sequentially
        for i, leg in enumerate(sorted_legs, start=1):
            logger.info(
                f"Executing leg {i}/{num_legs}: {leg.exchange} {leg.action} {leg.market_id}"
            )

            success = self._execute_leg(leg)

            if not success:
                logger.error(f"Leg {i} failed: {leg.exchange} {leg.market_id}")

                # Rollback all executed legs
                if executed_legs:
                    logger.warning(
                        f"Rolling back {len(executed_legs)} executed legs..."
                    )
                    self.rollback_handler.rollback_opportunity(executed_legs)

                return {
                    "success": False,
                    "type": ArbitrageType.MULTI_LEG.value,
                    "legs_executed": len(executed_legs),
                    "legs_failed": num_legs - len(executed_legs),
                    "profit": 0.0,
                    "error": f"Leg {i} execution failed, rolled back {len(executed_legs)} legs",
                    "timestamp": datetime.now(),
                }

            executed_legs.append(leg)
            logger.info(f"✓ Leg {i} executed successfully")

        # All legs successful
        return {
            "success": True,
            "type": ArbitrageType.MULTI_LEG.value,
            "legs_executed": num_legs,
            "legs_failed": 0,
            "profit": opportunity.expected_profit,
            "error": None,
            "timestamp": datetime.now(),
        }

    def execute(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """
        Router method that calls appropriate executor based on type

        Validates Kalshi-first rule before execution.
        Routes to type-specific executor.

        Args:
            opportunity: ArbitrageOpportunity to execute

        Returns:
            Execution result dictionary
        """
        # Validate Kalshi-first
        if not validate_kalshi_first(opportunity):
            logger.error("Rejecting opportunity: Kalshi-first validation failed")
            return {
                "success": False,
                "type": opportunity.type.value,
                "legs_executed": 0,
                "legs_failed": len(opportunity.legs),
                "profit": 0.0,
                "error": "Kalshi-first validation failed",
                "timestamp": datetime.now(),
            }

        # Route to appropriate executor
        if opportunity.type == ArbitrageType.TWO_WAY:
            return self.execute_two_way(opportunity)
        elif opportunity.type == ArbitrageType.THREE_WAY:
            return self.execute_three_way(opportunity)
        elif opportunity.type == ArbitrageType.MULTI_LEG:
            return self.execute_multi_leg(opportunity)
        else:
            return {
                "success": False,
                "type": opportunity.type.value,
                "legs_executed": 0,
                "legs_failed": len(opportunity.legs),
                "profit": 0.0,
                "error": f"Unknown arbitrage type: {opportunity.type}",
                "timestamp": datetime.now(),
            }

    def _execute_leg(self, leg: ArbitrageLeg) -> bool:
        """
        Execute a single leg (mock implementation)

        In production, this would call actual exchange APIs.
        For now, simulates successful execution.

        Args:
            leg: ArbitrageLeg to execute

        Returns:
            True if execution successful
        """
        # In production:
        # 1. Connect to exchange API
        # 2. Place order with leg parameters
        # 3. Wait for execution
        # 4. Verify fill
        # 5. Return success/failure

        # For now, simulate success
        return True
