"""
DEPRECATED FOR LIVE EXECUTION.

This module is NOT the source of truth for live trading.
Live execution state lives in ExecutionEngine -> PaperTradingEngine.

This module may be used for:
- legacy paths
- reporting
- backtests
- dashboard fallback
"""

"""
Position Tracking System for Trading Bot
Tracks all positions, their status, and P&L calculations
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging


class PositionStatus(Enum):
    """Position status enum"""

    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"
    EXPIRED = "expired"


class PositionSide(Enum):
    """Position side enum"""

    YES = "yes"
    NO = "no"
    BOTH = "both"  # For arbitrage positions


@dataclass
class Position:
    """Individual position data"""

    position_id: str
    market_id: str
    market_name: str
    side: str  # 'yes', 'no', or 'both' for arbitrage
    entry_price_yes: float
    entry_price_no: float
    size: float  # Position size in dollars
    entry_time: datetime
    status: str
    strategy: str
    expected_profit: float
    actual_profit: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_price_yes: Optional[float] = None
    exit_price_no: Optional[float] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["entry_time"] = self.entry_time.isoformat()
        if self.exit_time:
            data["exit_time"] = self.exit_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        """Create from dictionary"""
        data["entry_time"] = datetime.fromisoformat(data["entry_time"])
        if data.get("exit_time"):
            data["exit_time"] = datetime.fromisoformat(data["exit_time"])
        return cls(**data)


class PositionTracker:
    """Position tracking system"""

    def __init__(self, storage_path: str = "data/positions.json"):
        self.storage_path = storage_path
        self.positions: Dict[str, Position] = {}
        self.logger = logging.getLogger(__name__)
        self._load_positions()

    def _load_positions(self):
        """Load positions from storage"""
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for position_data in data:
                    position = Position.from_dict(position_data)
                    self.positions[position.position_id] = position
            self.logger.info(f"Loaded {len(self.positions)} positions from storage")
        except FileNotFoundError:
            self.logger.info("No existing positions found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading positions: {e}")

    def _save_positions(self):
        """Save positions to storage"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            with open(self.storage_path, "w") as f:
                data = [position.to_dict() for position in self.positions.values()]
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving positions: {e}")

    def open_position(
        self,
        market_id: str,
        market_name: str,
        side: str,
        entry_price_yes: float,
        entry_price_no: float,
        size: float,
        strategy: str,
        expected_profit: float,
        metadata: Optional[Dict] = None,
    ) -> Position:
        """Open a new position"""
        position = Position(
            position_id=str(uuid.uuid4()),
            market_id=market_id,
            market_name=market_name,
            side=side,
            entry_price_yes=entry_price_yes,
            entry_price_no=entry_price_no,
            size=size,
            entry_time=datetime.utcnow(),
            status=PositionStatus.OPEN.value,
            strategy=strategy,
            expected_profit=expected_profit,
            metadata=metadata or {},
        )

        self.positions[position.position_id] = position
        self._save_positions()

        self.logger.info(
            f"Opened position {position.position_id} for {market_name} "
            f"(${size:.2f}, expected profit: ${expected_profit:.2f})"
        )

        return position

    def close_position(
        self,
        position_id: str,
        exit_price_yes: float,
        exit_price_no: float,
        actual_profit: float,
    ) -> Optional[Position]:
        """Close a position"""
        if position_id not in self.positions:
            self.logger.error(f"Position {position_id} not found")
            return None

        position = self.positions[position_id]
        position.status = PositionStatus.CLOSED.value
        position.exit_time = datetime.utcnow()
        position.exit_price_yes = exit_price_yes
        position.exit_price_no = exit_price_no
        position.actual_profit = actual_profit

        self._save_positions()

        self.logger.info(
            f"Closed position {position_id} with profit ${actual_profit:.2f} "
            f"(expected: ${position.expected_profit:.2f})"
        )

        return position

    def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        return self.positions.get(position_id)

    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return [
            p for p in self.positions.values() if p.status == PositionStatus.OPEN.value
        ]

    def get_closed_positions(self) -> List[Position]:
        """Get all closed positions"""
        return [
            p
            for p in self.positions.values()
            if p.status == PositionStatus.CLOSED.value
        ]

    def get_positions_by_market(self, market_id: str) -> List[Position]:
        """Get all positions for a market"""
        return [p for p in self.positions.values() if p.market_id == market_id]

    def get_positions_by_strategy(self, strategy: str) -> List[Position]:
        """Get all positions for a strategy"""
        return [p for p in self.positions.values() if p.strategy == strategy]

    def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        return list(self.positions.values())

    def get_position_stats(self) -> Dict[str, Any]:
        """Get position statistics"""
        open_positions = self.get_open_positions()
        closed_positions = self.get_closed_positions()

        total_open_size = sum(p.size for p in open_positions)
        total_expected_profit = sum(p.expected_profit for p in open_positions)

        total_closed_profit = sum(
            p.actual_profit for p in closed_positions if p.actual_profit is not None
        )

        return {
            "total_positions": len(self.positions),
            "open_positions": len(open_positions),
            "closed_positions": len(closed_positions),
            "total_open_size": total_open_size,
            "total_expected_profit": total_expected_profit,
            "total_realized_profit": total_closed_profit,
        }


# Global instance
position_tracker = PositionTracker()
