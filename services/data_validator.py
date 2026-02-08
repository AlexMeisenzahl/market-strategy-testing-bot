"""
Data Validation Service

Ensure data is accurate and fresh before trading.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from logger import get_logger

logger = get_logger()


class DataValidator:
    """Ensure data is accurate and fresh"""

    def __init__(
        self,
        freshness_threshold_seconds: int = 5,
        price_discrepancy_threshold_pct: float = 1.0
    ):
        """
        Initialize data validator
        
        Args:
            freshness_threshold_seconds: Max age for fresh data
            price_discrepancy_threshold_pct: Max acceptable price difference
        """
        self.freshness_threshold = freshness_threshold_seconds
        self.price_threshold = price_discrepancy_threshold_pct
        
        # Cache for recent validations
        self.validation_cache = {}

    def validate_polymarket_price(
        self, 
        market_id: str,
        our_price: float,
        api_price: float = None
    ) -> Dict:
        """
        Validate price matches Polymarket
        
        Args:
            market_id: Market ID to validate
            our_price: Our cached/computed price
            api_price: Official API price (if available)
            
        Returns:
            Validation result
        """
        try:
            # If no API price provided, we can't validate
            if api_price is None:
                return {
                    'valid': True,  # Assume valid if we can't check
                    'market_id': market_id,
                    'our_price': our_price,
                    'api_price': None,
                    'discrepancy_pct': 0.0,
                    'reason': 'No API price available for validation'
                }
            
            # Calculate discrepancy
            if api_price == 0:
                discrepancy_pct = 100.0 if our_price != 0 else 0.0
            else:
                discrepancy_pct = abs((our_price - api_price) / api_price) * 100
            
            # Check if within threshold
            valid = discrepancy_pct <= self.price_threshold
            
            if not valid:
                logger.warning(
                    f"Price discrepancy for {market_id}: "
                    f"Our={our_price}, API={api_price}, "
                    f"Diff={discrepancy_pct:.2f}%"
                )
            
            return {
                'valid': valid,
                'market_id': market_id,
                'our_price': our_price,
                'api_price': api_price,
                'discrepancy_pct': round(discrepancy_pct, 2),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating price: {e}")
            return {
                'valid': False,
                'market_id': market_id,
                'error': str(e)
            }

    def check_data_freshness(
        self, 
        market_id: str,
        last_update_timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Check if data is fresh (<5 seconds old)
        
        Args:
            market_id: Market ID to check
            last_update_timestamp: When data was last updated
            
        Returns:
            True if fresh, False if stale
        """
        try:
            if last_update_timestamp is None:
                logger.warning(f"No timestamp for market {market_id}")
                return False
            
            # Calculate age
            age_seconds = (datetime.utcnow() - last_update_timestamp).total_seconds()
            
            is_fresh = age_seconds <= self.freshness_threshold
            
            if not is_fresh:
                logger.warning(
                    f"Stale data for {market_id}: {age_seconds:.1f}s old "
                    f"(threshold: {self.freshness_threshold}s)"
                )
            
            return is_fresh
            
        except Exception as e:
            logger.error(f"Error checking data freshness: {e}")
            return False

    def validate_market_liquidity(
        self,
        market_id: str,
        liquidity: float,
        min_liquidity: float = 1000.0
    ) -> bool:
        """
        Validate market has sufficient liquidity
        
        Args:
            market_id: Market ID to check
            liquidity: Current liquidity
            min_liquidity: Minimum required liquidity
            
        Returns:
            True if sufficient, False otherwise
        """
        try:
            sufficient = liquidity >= min_liquidity
            
            if not sufficient:
                logger.warning(
                    f"Insufficient liquidity for {market_id}: "
                    f"${liquidity:.2f} < ${min_liquidity:.2f}"
                )
            
            return sufficient
            
        except Exception as e:
            logger.error(f"Error validating liquidity: {e}")
            return False

    def validate_before_trade(
        self,
        market_id: str,
        our_price: float,
        api_price: float = None,
        last_update: datetime = None,
        liquidity: float = None,
        min_liquidity: float = 1000.0
    ) -> Dict:
        """
        Run all validations before executing trade
        
        Args:
            market_id: Market ID to validate
            our_price: Our cached price
            api_price: Official API price
            last_update: Last data update timestamp
            liquidity: Current liquidity
            min_liquidity: Minimum required liquidity
            
        Returns:
            Validation result with all checks
        """
        try:
            # Price validation
            price_validation = self.validate_polymarket_price(
                market_id, our_price, api_price
            )
            
            # Freshness check
            data_fresh = self.check_data_freshness(market_id, last_update)
            
            # Liquidity check
            liquidity_sufficient = True
            if liquidity is not None:
                liquidity_sufficient = self.validate_market_liquidity(
                    market_id, liquidity, min_liquidity
                )
            
            # Overall validation
            all_valid = (
                price_validation['valid'] and
                data_fresh and
                liquidity_sufficient
            )
            
            return {
                'valid': all_valid,
                'market_id': market_id,
                'price_validation': price_validation,
                'data_fresh': data_fresh,
                'liquidity_sufficient': liquidity_sufficient,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in pre-trade validation: {e}", exc_info=True)
            return {
                'valid': False,
                'market_id': market_id,
                'error': str(e)
            }

    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        try:
            # TODO: Track validation stats over time
            return {
                'total_validations': len(self.validation_cache),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting validation stats: {e}")
            return {'error': str(e)}


# Global instance
data_validator = DataValidator()
