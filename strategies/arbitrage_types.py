"""
Arbitrage Types Module

Defines arbitrage types (2-way, 3-way, multi-leg) and related data structures
for executing cross-exchange arbitrage strategies with Kalshi-first priority.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class ArbitrageType(Enum):
    """Types of arbitrage strategies supported"""

    TWO_WAY = "2-way"  # Simple arbitrage between 2 exchanges
    THREE_WAY = "3-way"  # Triangular arbitrage across 3 exchanges
    MULTI_LEG = "multi-leg"  # Complex arbitrage with 4+ legs


@dataclass
class ArbitrageLeg:
    """
    Represents a single leg of an arbitrage trade

    Attributes:
        exchange: Exchange name (e.g., "kalshi", "polymarket")
        action: "buy" or "sell"
        market_id: Market identifier
        price: Execution price
        quantity: Trade size
        order: Execution order (1 = first, 2 = second, etc.)
    """

    exchange: str
    action: str
    market_id: str
    price: float
    quantity: float
    order: int

    def __post_init__(self):
        """Validate leg data after initialization"""
        if self.action not in ["buy", "sell"]:
            raise ValueError(f"Action must be 'buy' or 'sell', got '{self.action}'")
        if self.price <= 0:
            raise ValueError(f"Price must be positive, got {self.price}")
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")
        if self.order < 1:
            raise ValueError(f"Order must be >= 1, got {self.order}")


@dataclass
class ArbitrageOpportunity:
    """
    Represents a complete arbitrage opportunity with multiple legs

    Attributes:
        type: Type of arbitrage (2-way, 3-way, multi-leg)
        legs: All legs in execution order
        expected_profit: Estimated profit
        timestamp: When opportunity was detected
        kalshi_first: Whether Kalshi is the first leg
    """

    type: ArbitrageType
    legs: List[ArbitrageLeg]
    expected_profit: float
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    kalshi_first: bool = field(init=False)

    def __post_init__(self):
        """Set kalshi_first based on legs"""
        if not self.legs:
            self.kalshi_first = False
        else:
            # Check if first leg is Kalshi
            first_leg = min(self.legs, key=lambda leg: leg.order)
            self.kalshi_first = first_leg.exchange.lower() == "kalshi"

    @property
    def num_legs(self) -> int:
        """Return number of legs in this opportunity"""
        return len(self.legs)

    @property
    def exchanges(self) -> List[str]:
        """Return list of unique exchanges involved"""
        return list(set(leg.exchange for leg in self.legs))

    def to_dict(self):
        """Convert opportunity to dictionary for logging"""
        return {
            "type": self.type.value,
            "num_legs": self.num_legs,
            "exchanges": self.exchanges,
            "expected_profit": self.expected_profit,
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, datetime)
                else self.timestamp
            ),
            "kalshi_first": self.kalshi_first,
            "legs": [
                {
                    "exchange": leg.exchange,
                    "action": leg.action,
                    "market_id": leg.market_id,
                    "price": leg.price,
                    "quantity": leg.quantity,
                    "order": leg.order,
                }
                for leg in sorted(self.legs, key=lambda l: l.order)
            ],
        }
