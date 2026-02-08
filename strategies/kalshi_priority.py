"""
Kalshi Priority Module

Ensures Kalshi exchange legs are always executed first in arbitrage opportunities.
This is a business rule that prioritizes Kalshi due to liquidity and reliability.
"""

from typing import List
import logging
from strategies.arbitrage_types import ArbitrageLeg, ArbitrageOpportunity


# Get logger for this module
logger = logging.getLogger(__name__)


def sort_legs_kalshi_first(legs: List[ArbitrageLeg]) -> List[ArbitrageLeg]:
    """
    Sort legs to put Kalshi legs first in execution order
    
    Always puts Kalshi legs first, preserving relative order of non-Kalshi legs.
    Updates the order attribute of each leg to reflect new execution sequence.
    
    Args:
        legs: List of ArbitrageLeg objects to sort
        
    Returns:
        List of ArbitrageLeg objects with Kalshi legs first
        
    Example:
        Input:  [polymarket(order=1), kalshi(order=2), binance(order=3)]
        Output: [kalshi(order=1), polymarket(order=2), binance(order=3)]
    """
    if not legs:
        return legs
    
    # Separate Kalshi and non-Kalshi legs
    kalshi_legs = [leg for leg in legs if leg.exchange.lower() == "kalshi"]
    other_legs = [leg for leg in legs if leg.exchange.lower() != "kalshi"]
    
    # Sort each group by their original order
    kalshi_legs.sort(key=lambda leg: leg.order)
    other_legs.sort(key=lambda leg: leg.order)
    
    # Combine with Kalshi first
    sorted_legs = kalshi_legs + other_legs
    
    # Update order numbers to reflect new sequence
    for i, leg in enumerate(sorted_legs, start=1):
        leg.order = i
    
    return sorted_legs


def validate_kalshi_first(opportunity: ArbitrageOpportunity) -> bool:
    """
    Validate that Kalshi leg is first (or no Kalshi leg exists)
    
    Returns True if the opportunity follows Kalshi-first rule:
    - If Kalshi leg exists, it must be the first leg (order=1)
    - If no Kalshi leg exists, validation passes
    
    Args:
        opportunity: ArbitrageOpportunity to validate
        
    Returns:
        True if valid (Kalshi first or no Kalshi), False otherwise
    """
    if not opportunity.legs:
        return True
    
    # Find all Kalshi legs
    kalshi_legs = [leg for leg in opportunity.legs if leg.exchange.lower() == "kalshi"]
    
    # If no Kalshi legs, validation passes
    if not kalshi_legs:
        return True
    
    # Find the first leg by order
    first_leg = min(opportunity.legs, key=lambda leg: leg.order)
    
    # Check if first leg is Kalshi
    is_valid = first_leg.exchange.lower() == "kalshi"
    
    if not is_valid:
        logger.warning(
            f"Kalshi-first validation failed: Opportunity has Kalshi leg but first leg is {first_leg.exchange}. "
            f"Type: {opportunity.type.value}, Expected profit: ${opportunity.expected_profit:.2f}"
        )
    
    return is_valid
