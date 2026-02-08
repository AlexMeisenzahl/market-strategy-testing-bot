"""
Rollback Handler Module

Handles rollback of failed arbitrage trades by reversing executed legs.
Rollback is "best effort" - logs failures but doesn't raise exceptions.
"""

from typing import Dict, List, Any
import logging
from strategies.arbitrage_types import ArbitrageLeg


# Get logger for this module
logger = logging.getLogger(__name__)


class RollbackHandler:
    """
    Handles rollback of failed arbitrage executions
    
    Reverses executed legs when an arbitrage opportunity fails mid-execution.
    Rollback is best-effort: individual rollback failures are logged but don't
    stop the rollback process.
    """
    
    def rollback_leg(self, leg: ArbitrageLeg) -> bool:
        """
        Reverse a single executed leg (buy → sell, sell → buy)
        
        This is a mock implementation that simulates rollback logic.
        In production, this would call actual exchange APIs to reverse trades.
        
        Args:
            leg: ArbitrageLeg to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Determine reverse action
            reverse_action = "sell" if leg.action == "buy" else "buy"
            
            logger.info(
                f"Rolling back leg: {leg.exchange} {leg.action} → {reverse_action} "
                f"(market: {leg.market_id}, quantity: {leg.quantity})"
            )
            
            # In production, this would:
            # 1. Create reverse order on the exchange
            # 2. Wait for execution
            # 3. Verify completion
            # For now, we simulate success
            
            logger.info(f"✓ Rollback successful for {leg.exchange} {leg.market_id}")
            return True
            
        except Exception as e:
            logger.error(
                f"✗ Rollback failed for {leg.exchange} {leg.market_id}: {e}"
            )
            return False
    
    def rollback_opportunity(self, executed_legs: List[ArbitrageLeg]) -> Dict[str, Any]:
        """
        Rollback all executed legs in reverse order
        
        Processes legs in reverse execution order (last executed first).
        Continues rollback even if individual legs fail.
        
        Args:
            executed_legs: List of ArbitrageLeg objects that were executed
            
        Returns:
            Dictionary with rollback results:
            {
                'total_legs': int,
                'successful_rollbacks': int,
                'failed_rollbacks': int,
                'rollback_details': List[Dict]
            }
        """
        if not executed_legs:
            logger.info("No legs to rollback")
            return {
                'total_legs': 0,
                'successful_rollbacks': 0,
                'failed_rollbacks': 0,
                'rollback_details': []
            }
        
        logger.info(f"Starting rollback of {len(executed_legs)} executed legs")
        
        # Sort legs in reverse execution order
        legs_to_rollback = sorted(executed_legs, key=lambda leg: leg.order, reverse=True)
        
        successful = 0
        failed = 0
        rollback_details = []
        
        for leg in legs_to_rollback:
            success = self.rollback_leg(leg)
            
            rollback_details.append({
                'exchange': leg.exchange,
                'market_id': leg.market_id,
                'action': leg.action,
                'order': leg.order,
                'success': success
            })
            
            if success:
                successful += 1
            else:
                failed += 1
        
        result = {
            'total_legs': len(executed_legs),
            'successful_rollbacks': successful,
            'failed_rollbacks': failed,
            'rollback_details': rollback_details
        }
        
        logger.info(
            f"Rollback complete: {successful} successful, {failed} failed "
            f"out of {len(executed_legs)} total"
        )
        
        return result
