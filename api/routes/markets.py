"""
Market Routes

Handles market data retrieval and search functionality.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional

from api.models.schemas import MarketResponse, MarketListResponse, MarketSearchRequest
from api.middleware.auth import get_current_user
from api.server import get_bot
from logger import get_logger

router = APIRouter()
logger = get_logger()


@router.get("", response_model=MarketListResponse)
async def list_markets(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    List all available markets

    Args:
        page: Page number
        per_page: Results per page
        category: Optional category filter
        current_user: Authenticated user

    Returns:
        Paginated list of markets
    """
    try:
        bot = get_bot()

        # Get markets from bot (this would need to be implemented in the bot)
        # For now, return mock data
        markets = []

        return MarketListResponse(
            markets=markets, total=len(markets), page=page, per_page=per_page
        )

    except Exception as e:
        logger.log_error(f"Failed to list markets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve markets")


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(market_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get specific market details

    Args:
        market_id: Market identifier
        current_user: Authenticated user

    Returns:
        Market details
    """
    try:
        bot = get_bot()

        # Get market from bot
        # Mock response for now
        raise HTTPException(status_code=404, detail="Market not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(f"Failed to get market {market_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve market")


@router.get("/search", response_model=MarketListResponse)
async def search_markets(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    Search markets by query

    Args:
        q: Search query
        limit: Maximum results
        current_user: Authenticated user

    Returns:
        Matching markets
    """
    try:
        bot = get_bot()

        # Search markets
        markets = []

        return MarketListResponse(
            markets=markets, total=len(markets), page=1, per_page=limit
        )

    except Exception as e:
        logger.log_error(f"Market search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")
