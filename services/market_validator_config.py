"""
Market Validator Configuration

Confidence level thresholds for market validation.
Defines when discrepancies are considered EXTREME, HIGH, or MEDIUM.
"""

from typing import Dict, Any
from enum import Enum


class DiscrepancyLevel(Enum):
    """Discrepancy severity levels"""
    EXTREME = 'extreme'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    NONE = 'none'


class ConfidenceLevel(Enum):
    """Confidence levels for predictions"""
    VERY_HIGH = 'very_high'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


# Threshold configurations for discrepancy detection
DISCREPANCY_THRESHOLDS = {
    'EXTREME': {
        'market_price_max': 0.80,  # Market price must be below 80%
        'confidence': ConfidenceLevel.VERY_HIGH,
        'description': 'Extreme discrepancy - very strong arbitrage opportunity'
    },
    'HIGH': {
        'market_price_max': 0.90,  # Market price must be below 90%
        'confidence': ConfidenceLevel.HIGH,
        'description': 'High discrepancy - strong arbitrage opportunity'
    },
    'MEDIUM': {
        'market_price_max': 0.93,  # Market price must be below 93%
        'confidence': ConfidenceLevel.MEDIUM,
        'description': 'Medium discrepancy - potential arbitrage opportunity'
    }
}

# Near threshold configuration
NEAR_THRESHOLD_CONFIG = {
    'percentage_range': 0.05,  # Within 5% of threshold
    'expected_market_price': 0.50,  # Expected market price when near threshold
    'confidence': ConfidenceLevel.MEDIUM,
    'description': 'Price near threshold - outcome uncertain'
}


def get_discrepancy_level(
    current_price: float,
    threshold: float,
    market_yes_price: float,
    direction: str
) -> Dict[str, Any]:
    """
    Determine the discrepancy level between reality and market pricing.
    
    Args:
        current_price: Current actual price of the asset
        threshold: Threshold price from the market question
        market_yes_price: Market's YES probability (0-1)
        direction: 'above' or 'below'
        
    Returns:
        Dictionary with:
            - level (DiscrepancyLevel): Severity of discrepancy
            - confidence (ConfidenceLevel): Confidence in the prediction
            - expected_outcome (bool): Expected resolution (True/False)
            - market_price (float): Market's YES price
            - discrepancy (float): Absolute difference between expected and market price
            - profit_potential (float): Potential profit from arbitrage
            - description (str): Human-readable description
    """
    # Determine if reality matches the YES outcome
    if direction == 'above':
        reality_is_yes = current_price > threshold
    else:  # 'below'
        reality_is_yes = current_price < threshold
    
    # Check if price is near threshold (within 5%)
    price_diff_percent = abs(current_price - threshold) / threshold
    is_near_threshold = price_diff_percent <= NEAR_THRESHOLD_CONFIG['percentage_range']
    
    if is_near_threshold:
        # Near threshold - outcome uncertain
        return {
            'level': DiscrepancyLevel.LOW,
            'confidence': NEAR_THRESHOLD_CONFIG['confidence'],
            'expected_outcome': None,  # Uncertain
            'market_price': market_yes_price,
            'discrepancy': abs(NEAR_THRESHOLD_CONFIG['expected_market_price'] - market_yes_price),
            'profit_potential': 0.0,
            'description': NEAR_THRESHOLD_CONFIG['description'],
            'reason': 'Price within 5% of threshold - outcome uncertain'
        }
    
    # Expected market price based on reality
    expected_market_price = 0.95 if reality_is_yes else 0.05
    
    # Calculate discrepancy
    discrepancy = abs(expected_market_price - market_yes_price)
    
    # Determine discrepancy level
    level = DiscrepancyLevel.NONE
    confidence = ConfidenceLevel.LOW
    description = 'No significant discrepancy'
    
    if reality_is_yes:
        # Reality says YES, check if market is underpricing
        if market_yes_price < DISCREPANCY_THRESHOLDS['EXTREME']['market_price_max']:
            level = DiscrepancyLevel.EXTREME
            confidence = DISCREPANCY_THRESHOLDS['EXTREME']['confidence']
            description = DISCREPANCY_THRESHOLDS['EXTREME']['description']
        elif market_yes_price < DISCREPANCY_THRESHOLDS['HIGH']['market_price_max']:
            level = DiscrepancyLevel.HIGH
            confidence = DISCREPANCY_THRESHOLDS['HIGH']['confidence']
            description = DISCREPANCY_THRESHOLDS['HIGH']['description']
        elif market_yes_price < DISCREPANCY_THRESHOLDS['MEDIUM']['market_price_max']:
            level = DiscrepancyLevel.MEDIUM
            confidence = DISCREPANCY_THRESHOLDS['MEDIUM']['confidence']
            description = DISCREPANCY_THRESHOLDS['MEDIUM']['description']
        else:
            level = DiscrepancyLevel.LOW
    else:
        # Reality says NO, check if market is overpricing YES
        market_no_price = 1 - market_yes_price
        if market_no_price < DISCREPANCY_THRESHOLDS['EXTREME']['market_price_max']:
            level = DiscrepancyLevel.EXTREME
            confidence = DISCREPANCY_THRESHOLDS['EXTREME']['confidence']
            description = DISCREPANCY_THRESHOLDS['EXTREME']['description']
        elif market_no_price < DISCREPANCY_THRESHOLDS['HIGH']['market_price_max']:
            level = DiscrepancyLevel.HIGH
            confidence = DISCREPANCY_THRESHOLDS['HIGH']['confidence']
            description = DISCREPANCY_THRESHOLDS['HIGH']['description']
        elif market_no_price < DISCREPANCY_THRESHOLDS['MEDIUM']['market_price_max']:
            level = DiscrepancyLevel.MEDIUM
            confidence = DISCREPANCY_THRESHOLDS['MEDIUM']['confidence']
            description = DISCREPANCY_THRESHOLDS['MEDIUM']['description']
        else:
            level = DiscrepancyLevel.LOW
    
    # Calculate profit potential (simplified)
    if level != DiscrepancyLevel.NONE and level != DiscrepancyLevel.LOW:
        if reality_is_yes:
            profit_potential = (1 - market_yes_price) / market_yes_price if market_yes_price > 0 else 0
        else:
            profit_potential = (market_yes_price) / (1 - market_yes_price) if market_yes_price < 1 else 0
    else:
        profit_potential = 0.0
    
    return {
        'level': level,
        'confidence': confidence,
        'expected_outcome': reality_is_yes,
        'market_price': market_yes_price,
        'discrepancy': discrepancy,
        'profit_potential': profit_potential,
        'description': description,
        'reason': _get_reason(reality_is_yes, current_price, threshold, direction)
    }


def _get_reason(reality_is_yes: bool, current_price: float, threshold: float, direction: str) -> str:
    """
    Generate a human-readable reason for the discrepancy.
    
    Args:
        reality_is_yes: Whether reality matches YES outcome
        current_price: Current price
        threshold: Threshold price
        direction: 'above' or 'below'
        
    Returns:
        Human-readable reason string
    """
    if direction == 'above':
        if reality_is_yes:
            return f"Price ${current_price:,.2f} is already above threshold ${threshold:,.2f}"
        else:
            return f"Price ${current_price:,.2f} is below threshold ${threshold:,.2f}"
    else:  # 'below'
        if reality_is_yes:
            return f"Price ${current_price:,.2f} is already below threshold ${threshold:,.2f}"
        else:
            return f"Price ${current_price:,.2f} is above threshold ${threshold:,.2f}"


def get_confidence_score(confidence: ConfidenceLevel) -> float:
    """
    Convert confidence level to numeric score (0-1).
    
    Args:
        confidence: ConfidenceLevel enum
        
    Returns:
        Numeric confidence score
    """
    scores = {
        ConfidenceLevel.VERY_HIGH: 0.95,
        ConfidenceLevel.HIGH: 0.85,
        ConfidenceLevel.MEDIUM: 0.70,
        ConfidenceLevel.LOW: 0.50
    }
    return scores.get(confidence, 0.50)


def get_minimum_profit_threshold(confidence: ConfidenceLevel) -> float:
    """
    Get minimum profit threshold required for given confidence level.
    
    Args:
        confidence: ConfidenceLevel enum
        
    Returns:
        Minimum profit threshold as decimal (e.g., 0.05 = 5%)
    """
    thresholds = {
        ConfidenceLevel.VERY_HIGH: 0.02,  # 2% minimum for very high confidence
        ConfidenceLevel.HIGH: 0.05,       # 5% minimum for high confidence
        ConfidenceLevel.MEDIUM: 0.10,     # 10% minimum for medium confidence
        ConfidenceLevel.LOW: 0.20         # 20% minimum for low confidence
    }
    return thresholds.get(confidence, 0.10)
