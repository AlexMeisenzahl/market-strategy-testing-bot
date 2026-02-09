"""
Trade Routes

Handles trade execution and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from api.models.schemas import TradeRequest, TradeResponse, TradeStatus
from api.middleware.auth import get_current_user
from api.server import get_bot
from logger import get_logger
from datetime import datetime
import uuid

router = APIRouter()
logger = get_logger()


@router.post("", response_model=TradeResponse)
async def execute_trade(
    request: TradeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a trade
    
    Args:
        request: Trade request details
        current_user: Authenticated user
        
    Returns:
        Trade execution response
    """
    try:
        bot = get_bot()
        username = current_user.get("username")
        
        logger.log_info(
            f"Trade request from {username}: {request.side} {request.amount} "
            f"on market {request.market_id}"
        )
        
        # In paper trading mode, simulate trade execution
        trade_id = str(uuid.uuid4())
        
        response = TradeResponse(
            trade_id=trade_id,
            market_id=request.market_id,
            market_name="Mock Market",  # Would fetch from bot
            side=request.side,
            order_type=request.order_type,
            amount=request.amount,
            price=request.price or 0.5,
            status=TradeStatus.EXECUTED,
            created_at=datetime.now(),
            executed_at=datetime.now()
        )
        
        logger.log_info(f"Trade executed: {trade_id}")
        
        return response
        
    except Exception as e:
        logger.log_error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail="Trade execution failed")


@router.delete("/{trade_id}")
async def cancel_trade(
    trade_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a pending trade
    
    Args:
        trade_id: Trade identifier
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    try:
        bot = get_bot()
        username = current_user.get("username")
        
        logger.log_info(f"Cancel trade request from {username}: {trade_id}")
        
        # Cancel trade logic would go here
        
        return {"message": "Trade cancelled successfully", "trade_id": trade_id}
        
    except Exception as e:
        logger.log_error(f"Trade cancellation failed: {e}")
        raise HTTPException(status_code=500, detail="Trade cancellation failed")
