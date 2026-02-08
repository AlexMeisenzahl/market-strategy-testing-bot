"""
Market Validator - Validate prediction markets against cryptocurrency reality

This service extracts crypto information from market names and validates whether
prediction market prices accurately reflect current cryptocurrency prices.

Example:
    Market: "Will Bitcoin be above $100,000 on Feb 8?"
    Current BTC Price: $105,234
    Market YES Price: 0.42 (42%)

    Result: MISPRICED - BTC is already above $100k but market only at 42%
            → Opportunity to BUY YES (58% profit potential)
"""

import re
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime


class MarketValidator:
    """
    Validate prediction markets against current crypto prices

    Features:
    - Parse market names to extract crypto info (symbol, threshold, direction)
    - Compare market probability to reality
    - Detect mispricing opportunities
    - Calculate profit potential
    - Provide confidence levels
    """

    # Symbol patterns for detection
    SYMBOL_PATTERNS = {
        "BTC": ["bitcoin", "btc"],
        "ETH": ["ethereum", "eth", "ether"],
        "SOL": ["solana", "sol"],
        "XRP": ["xrp", "ripple"],
        "ADA": ["cardano", "ada"],
        "DOT": ["polkadot", "dot"],
        "AVAX": ["avalanche", "avax"],
        "MATIC": ["polygon", "matic"],
        "DOGE": ["dogecoin", "doge"],
        "LTC": ["litecoin", "ltc"],
    }

    def __init__(self, logger=None):
        """
        Initialize market validator

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def validate_market_against_reality(
        self, market: Dict, current_prices: Dict[str, Dict]
    ) -> Optional[Dict]:
        """
        Validate a prediction market against current crypto prices

        Args:
            market: Market data dict with keys: market_name, yes_price, no_price
            current_prices: Dictionary of symbol -> price data from CryptoPriceManager

        Returns:
            Validation result dictionary or None if not a crypto market

        Example:
            >>> validator = MarketValidator()
            >>> market = {
            ...     'market_name': 'Will Bitcoin be above $100,000 on Feb 8?',
            ...     'yes_price': 0.42,
            ...     'no_price': 0.58
            ... }
            >>> prices = {'BTC': {'price_usd': Decimal('105234.56')}}
            >>> result = validator.validate_market_against_reality(market, prices)
            >>> print(result['valid'])  # False
            >>> print(result['opportunity'])  # 'BUY YES'
            >>> print(result['profit_potential_pct'])  # 58
        """
        market_name = market.get("market_name", "")

        # Extract crypto information from market name
        crypto_info = self._extract_crypto_info(market_name)

        if not crypto_info:
            # Not a crypto-related market
            return None

        symbol, threshold, direction = crypto_info

        # Check if we have current price for this symbol
        if symbol not in current_prices:
            if self.logger:
                self.logger.log_warning(f"No current price available for {symbol}")
            return None

        current_price = current_prices[symbol]["price_usd"]
        yes_price = Decimal(str(market.get("yes_price", 0)))
        no_price = Decimal(str(market.get("no_price", 0)))

        # Determine reality: has the condition been met?
        reality_met = self._check_condition(current_price, threshold, direction)

        # Calculate expected probability based on reality
        if reality_met:
            # Condition is already met, YES should be ~100% (or very high)
            expected_yes_price = Decimal("0.95")  # Allow for some uncertainty
        else:
            # Condition not met, need to estimate based on distance to threshold
            distance_pct = (
                abs(float(current_price - threshold)) / float(threshold) * 100
            )

            if direction == "above":
                if current_price < threshold:
                    # Below threshold, probability depends on distance
                    if distance_pct > 20:
                        expected_yes_price = Decimal("0.20")  # Far below
                    elif distance_pct > 10:
                        expected_yes_price = Decimal("0.35")  # Moderately below
                    else:
                        expected_yes_price = Decimal("0.45")  # Close to threshold
                else:
                    expected_yes_price = Decimal("0.95")  # Above threshold
            else:  # below
                if current_price > threshold:
                    # Above threshold, probability depends on distance
                    if distance_pct > 20:
                        expected_yes_price = Decimal("0.20")  # Far above
                    elif distance_pct > 10:
                        expected_yes_price = Decimal("0.35")  # Approaching threshold
                    else:
                        expected_yes_price = Decimal("0.45")  # Close to threshold
                else:
                    expected_yes_price = Decimal("0.95")  # Below threshold

        # Calculate discrepancy
        price_discrepancy = abs(expected_yes_price - yes_price)
        discrepancy_pct = float(price_discrepancy) * 100

        # Determine discrepancy level
        if discrepancy_pct > 40:
            discrepancy_level = "extreme"
            confidence = "very_high"
        elif discrepancy_pct > 25:
            discrepancy_level = "high"
            confidence = "high"
        elif discrepancy_pct > 15:
            discrepancy_level = "medium"
            confidence = "medium"
        elif discrepancy_pct > 5:
            discrepancy_level = "low"
            confidence = "low"
        else:
            discrepancy_level = "aligned"
            confidence = "none"

        # Determine if market is valid (correctly priced)
        is_valid = discrepancy_level in ["aligned", "low"]

        # Determine opportunity (if any)
        opportunity = None
        profit_potential_pct = 0

        if not is_valid:
            if expected_yes_price > yes_price:
                opportunity = "BUY YES"
                profit_potential_pct = float(expected_yes_price - yes_price) * 100
            else:
                opportunity = "BUY NO"
                profit_potential_pct = float(expected_yes_price - yes_price) * 100 * -1

        # Build reason string
        direction_text = "above" if direction == "above" else "below"
        threshold_str = f"${float(threshold):,.0f}"
        current_str = f"${float(current_price):,.0f}"

        if reality_met:
            reason = f"{symbol} is at {current_str} ({direction_text} {threshold_str}) but market only {float(yes_price)*100:.0f}%"
        else:
            opposite_dir = "below" if direction == "above" else "above"
            reason = f"{symbol} is at {current_str} ({opposite_dir} {threshold_str}) but market at {float(yes_price)*100:.0f}%"

        return {
            "valid": is_valid,
            "symbol": symbol,
            "threshold": float(threshold),
            "direction": direction,
            "current_price": float(current_price),
            "reality_met": reality_met,
            "market_yes_price": float(yes_price),
            "expected_yes_price": float(expected_yes_price),
            "discrepancy": discrepancy_level,
            "discrepancy_pct": discrepancy_pct,
            "reason": reason,
            "opportunity": opportunity,
            "confidence": confidence,
            "profit_potential_pct": profit_potential_pct,
            "timestamp": datetime.now().isoformat(),
        }

    def _extract_crypto_info(
        self, market_name: str
    ) -> Optional[Tuple[str, Decimal, str]]:
        """
        Extract crypto symbol, threshold, and direction from market name

        Args:
            market_name: Market name/question

        Returns:
            Tuple of (symbol, threshold, direction) or None

        Example:
            >>> validator = MarketValidator()
            >>> info = validator._extract_crypto_info("Will Bitcoin be above $100,000?")
            >>> print(info)  # ('BTC', Decimal('100000'), 'above')
        """
        market_lower = market_name.lower()

        # Detect crypto symbol
        symbol = None
        for sym, patterns in self.SYMBOL_PATTERNS.items():
            if any(pattern in market_lower for pattern in patterns):
                symbol = sym
                break

        if not symbol:
            return None

        # Extract threshold (price level)
        # Patterns: $100,000 | 100k | $100k | 100000
        threshold_patterns = [
            r"\$?([\d,]+)",  # Matches numbers like 100,000 or 100
        ]

        threshold = None
        for pattern in threshold_patterns:
            matches = re.finditer(pattern, market_lower)
            for match_obj in matches:
                match = match_obj.group(1)
                num_str = match.replace(",", "")
                try:
                    num = float(num_str)
                    # Check for 'k' multiplier immediately after the matched number
                    match_end = match_obj.end()
                    if (
                        match_end < len(market_lower)
                        and market_lower[match_end] == "k"
                        and num < 1000
                    ):
                        num *= 1000
                    if num >= 1000:  # Reasonable crypto price threshold
                        threshold = Decimal(str(int(num)))
                        break
                except:
                    continue
            if threshold:
                break

        if not threshold:
            return None

        # Detect direction (above/below)
        direction = None
        if any(
            word in market_lower for word in ["above", "over", "higher", "exceed", ">"]
        ):
            direction = "above"
        elif any(
            word in market_lower for word in ["below", "under", "lower", "less", "<"]
        ):
            direction = "below"

        if not direction:
            # Default to 'above' if not specified
            direction = "above"

        return (symbol, threshold, direction)

    def _check_condition(
        self, current_price: Decimal, threshold: Decimal, direction: str
    ) -> bool:
        """
        Check if condition is met based on current price

        Args:
            current_price: Current crypto price
            threshold: Threshold price
            direction: 'above' or 'below'

        Returns:
            True if condition is met
        """
        if direction == "above":
            return current_price > threshold
        else:  # below
            return current_price < threshold

    def is_crypto_market(self, market_name: str) -> bool:
        """
        Check if a market is crypto-related

        Args:
            market_name: Market name/question

        Returns:
            True if market is crypto-related
        """
        return self._extract_crypto_info(market_name) is not None
