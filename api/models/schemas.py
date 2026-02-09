"""
API Models and Schemas

Pydantic models for request/response validation in the Mobile Backend API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Order side enumeration"""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration"""

    MARKET = "market"
    LIMIT = "limit"


class PositionStatus(str, Enum):
    """Position status enumeration"""

    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"


class TradeStatus(str, Enum):
    """Trade status enumeration"""

    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


# Authentication Schemas
class LoginRequest(BaseModel):
    """Login request schema"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""

    refresh_token: str


# Bot Status Schemas
class BotStatusResponse(BaseModel):
    """Bot status response schema"""

    status: str  # running, paused, stopped
    uptime_seconds: int
    balance: float
    active_strategies: List[str]
    active_positions: int
    total_trades: int
    daily_pnl: float
    total_pnl: float


class HealthResponse(BaseModel):
    """Health check response schema"""

    status: str = "healthy"
    timestamp: datetime
    version: str


# Market Schemas
class MarketResponse(BaseModel):
    """Market response schema"""

    id: str
    question: str
    description: Optional[str] = None
    yes_price: float
    no_price: float
    volume: float
    liquidity: float
    end_date: Optional[datetime] = None
    tags: List[str] = []


class MarketListResponse(BaseModel):
    """Market list response schema"""

    markets: List[MarketResponse]
    total: int
    page: int
    per_page: int


class MarketSearchRequest(BaseModel):
    """Market search request schema"""

    query: str = Field(..., min_length=1)
    limit: int = Field(default=50, ge=1, le=100)


# Trading Schemas
class TradeRequest(BaseModel):
    """Trade request schema"""

    market_id: str
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    amount: float = Field(..., gt=0)
    price: Optional[float] = Field(None, ge=0, le=1)
    strategy: Optional[str] = None

    @validator("price")
    def validate_price_for_limit(cls, v, values):
        if values.get("order_type") == OrderType.LIMIT and v is None:
            raise ValueError("Price is required for limit orders")
        return v


class TradeResponse(BaseModel):
    """Trade response schema"""

    trade_id: str
    market_id: str
    market_name: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: float
    status: TradeStatus
    created_at: datetime
    executed_at: Optional[datetime] = None


class CancelTradeRequest(BaseModel):
    """Cancel trade request schema"""

    trade_id: str


# Position Schemas
class PositionResponse(BaseModel):
    """Position response schema"""

    position_id: str
    market_id: str
    market_name: str
    side: str
    entry_price: float
    current_price: float
    size: float
    pnl: float
    pnl_percent: float
    opened_at: datetime
    status: PositionStatus


class PositionListResponse(BaseModel):
    """Position list response schema"""

    positions: List[PositionResponse]
    total: int


class ClosePositionRequest(BaseModel):
    """Close position request schema"""

    position_id: str
    amount: Optional[float] = None  # If None, close entire position


# Strategy Schemas
class StrategyStatus(str, Enum):
    """Strategy status enumeration"""

    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class StrategyResponse(BaseModel):
    """Strategy response schema"""

    name: str
    display_name: str
    status: StrategyStatus
    description: str
    opportunities_found: int
    trades_executed: int
    pnl: float
    win_rate: float


class StrategyListResponse(BaseModel):
    """Strategy list response schema"""

    strategies: List[StrategyResponse]


class StrategyConfigResponse(BaseModel):
    """Strategy configuration response schema"""

    name: str
    config: Dict[str, Any]


class StrategyConfigUpdateRequest(BaseModel):
    """Strategy configuration update request schema"""

    config: Dict[str, Any]


# History Schemas
class TradeHistoryItem(BaseModel):
    """Trade history item schema"""

    trade_id: str
    market_name: str
    side: OrderSide
    amount: float
    price: float
    pnl: float
    strategy: Optional[str] = None
    executed_at: datetime


class TradeHistoryResponse(BaseModel):
    """Trade history response schema"""

    trades: List[TradeHistoryItem]
    total: int
    page: int
    per_page: int


class PnLDataPoint(BaseModel):
    """P&L data point schema"""

    timestamp: datetime
    pnl: float
    cumulative_pnl: float


class PnLHistoryResponse(BaseModel):
    """P&L history response schema"""

    data_points: List[PnLDataPoint]
    total_pnl: float
    daily_pnl: float
    weekly_pnl: float
    monthly_pnl: float


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    """WebSocket message schema"""

    type: str  # trade, position, market, strategy, status
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


# Error Response Schema
class ErrorResponse(BaseModel):
    """Error response schema"""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
