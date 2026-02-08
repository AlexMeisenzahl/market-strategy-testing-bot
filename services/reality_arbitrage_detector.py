"""
Reality Arbitrage Detector - 6th Arbitrage Type

Detects when prediction markets are mispriced compared to current crypto reality.
This is the most profitable arbitrage type when crypto conditions are already met
but markets haven't updated to reflect reality.

Example:
    BTC is at $105,000 (above $100k threshold)
    Market "Will BTC be above $100k?" is priced at YES=42%, NO=58%
    → EXTREME opportunity: BUY YES for guaranteed ~58% profit!
"""

from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.market_validator import MarketValidator
from services.crypto_price_manager import CryptoPriceManager


class RealityArbitrageDetector:
    """
    Detect reality-based arbitrage opportunities

    Features:
    - Scan all active markets for crypto-related questions
    - Validate each against current prices
    - Filter for high-confidence opportunities only
    - Tag as 6th arbitrage type: "Reality-Based"
    """

    def __init__(self, logger=None, config: Dict = None):
        """
        Initialize reality arbitrage detector

        Args:
            logger: Logger instance
            config: Configuration dictionary
        """
        self.logger = logger
        self.config = config or {}

        # Initialize services
        self.price_manager = CryptoPriceManager(logger=logger, config=config)
        self.validator = MarketValidator(logger=logger)

        # Configuration
        reality_config = (
            self.config.get("strategies", {})
            .get("polymarket_arbitrage", {})
            .get("arbitrage_types", {})
            .get("reality_based", {})
        )
        self.enabled = reality_config.get("enabled", True)
        self.min_profit_pct = Decimal(str(reality_config.get("min_profit_pct", 5.0)))
        self.min_confidence = reality_config.get(
            "min_confidence", "high"
        )  # 'medium', 'high', 'very_high'

        # Confidence level ordering
        self.confidence_levels = {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "very_high": 4,
        }

    def check_all_markets(self, markets: List[Dict]) -> List[Dict]:
        """
        Check all markets for reality-based arbitrage opportunities

        Args:
            markets: List of market dictionaries with keys:
                     - market_id, market_name, yes_price, no_price

        Returns:
            List of reality arbitrage opportunity dictionaries

        Example:
            >>> detector = RealityArbitrageDetector(logger=logger)
            >>> markets = [
            ...     {'market_id': '123', 'market_name': 'Will BTC be above $100k?',
            ...      'yes_price': 0.42, 'no_price': 0.58}
            ... ]
            >>> opportunities = detector.check_all_markets(markets)
            >>> for opp in opportunities:
            ...     print(f"{opp['market_name']}: {opp['opportunity']} - {opp['profit_potential_pct']:.0f}% profit")
        """
        if not self.enabled:
            if self.logger:
                self.logger.log_info("Reality arbitrage detection is disabled")
            return []

        opportunities = []

        # Filter to crypto-related markets only
        crypto_markets = [
            m
            for m in markets
            if self.validator.is_crypto_market(m.get("market_name", ""))
        ]

        if not crypto_markets:
            if self.logger:
                self.logger.log_info("No crypto-related markets found")
            return []

        if self.logger:
            self.logger.log_info(
                f"Checking {len(crypto_markets)} crypto markets for reality arbitrage"
            )

        # Get current crypto prices for all symbols we need
        symbols_needed = self._get_symbols_from_markets(crypto_markets)
        current_prices = self.price_manager.get_current_prices(symbols_needed)

        if not current_prices:
            if self.logger:
                self.logger.log_warning("Failed to fetch current crypto prices")
            return []

        # Validate each market
        for market in crypto_markets:
            validation = self.validator.validate_market_against_reality(
                market, current_prices
            )

            if not validation:
                continue

            # Check if this is a real opportunity
            if not validation["valid"] and validation["opportunity"]:
                # Check minimum profit requirement
                profit_pct = Decimal(str(validation["profit_potential_pct"]))
                if profit_pct < self.min_profit_pct:
                    continue

                # Check minimum confidence requirement
                confidence = validation["confidence"]
                if self.confidence_levels.get(
                    confidence, 0
                ) < self.confidence_levels.get(self.min_confidence, 0):
                    continue

                # This is a valid reality arbitrage opportunity!
                opportunity = {
                    "type": "reality_based",
                    "market_id": market.get("market_id"),
                    "market_name": market.get("market_name"),
                    "symbol": validation["symbol"],
                    "current_price": validation["current_price"],
                    "threshold": validation["threshold"],
                    "direction": validation["direction"],
                    "reality_met": validation["reality_met"],
                    "market_yes_price": validation["market_yes_price"],
                    "market_no_price": market.get(
                        "no_price", 1 - validation["market_yes_price"]
                    ),
                    "expected_yes_price": validation["expected_yes_price"],
                    "opportunity": validation["opportunity"],
                    "profit_potential_pct": validation["profit_potential_pct"],
                    "confidence": confidence,
                    "discrepancy": validation["discrepancy"],
                    "reason": validation["reason"],
                    "detected_at": datetime.now().isoformat(),
                }

                opportunities.append(opportunity)

                if self.logger:
                    self.logger.log_info(
                        f"🎯 Reality Arbitrage: {market.get('market_name')} - "
                        f"{validation['opportunity']} ({validation['profit_potential_pct']:.1f}% profit, "
                        f"{confidence} confidence)"
                    )

        if self.logger and opportunities:
            self.logger.log_info(
                f"Found {len(opportunities)} reality arbitrage opportunities"
            )

        return opportunities

    def _get_symbols_from_markets(self, markets: List[Dict]) -> List[str]:
        """
        Extract unique crypto symbols from market names

        Args:
            markets: List of market dictionaries

        Returns:
            List of unique symbols
        """
        symbols = set()

        for market in markets:
            market_name = market.get("market_name", "")
            crypto_info = self.validator._extract_crypto_info(market_name)
            if crypto_info:
                symbol, _, _ = crypto_info
                symbols.add(symbol)

        return list(symbols)

    def check_single_market(self, market: Dict) -> Optional[Dict]:
        """
        Check a single market for reality arbitrage

        Args:
            market: Market dictionary

        Returns:
            Opportunity dictionary or None
        """
        opportunities = self.check_all_markets([market])
        return opportunities[0] if opportunities else None
