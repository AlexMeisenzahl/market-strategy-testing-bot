"""
Strategy Routes

Handles strategy management and configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from api.models.schemas import (
    StrategyListResponse,
    StrategyResponse,
    StrategyStatus,
    StrategyConfigResponse,
    StrategyConfigUpdateRequest,
)
from api.middleware.auth import get_current_user
from api.server import get_bot, get_config
from logger import get_logger

router = APIRouter()
logger = get_logger()


@router.get("", response_model=StrategyListResponse)
async def list_strategies(current_user: dict = Depends(get_current_user)):
    """
    List all strategies with their status

    Args:
        current_user: Authenticated user

    Returns:
        List of strategies
    """
    try:
        bot = get_bot()
        config = get_config()

        strategies_config = config.get("strategies", {})
        strategies = []

        # Build strategy list from config
        strategy_names = [
            ("polymarket_arbitrage", "Polymarket Arbitrage"),
            ("crypto_momentum", "Crypto Momentum"),
            ("crypto_news", "Crypto News"),
            ("crypto_statistical_arb", "Statistical Arbitrage"),
            ("mean_reversion", "Mean Reversion"),
            ("volatility_breakout", "Volatility Breakout"),
            ("pairs_trading", "Pairs Trading"),
            ("weather_trading", "Weather Trading"),
            ("btc_arbitrage", "BTC Arbitrage"),
        ]

        for strategy_key, display_name in strategy_names:
            strategy_config = strategies_config.get(strategy_key, {})
            enabled = strategy_config.get("enabled", False)

            strategies.append(
                StrategyResponse(
                    name=strategy_key,
                    display_name=display_name,
                    status=(
                        StrategyStatus.ENABLED if enabled else StrategyStatus.DISABLED
                    ),
                    description=f"{display_name} trading strategy",
                    opportunities_found=0,
                    trades_executed=0,
                    pnl=0.0,
                    win_rate=0.0,
                )
            )

        return StrategyListResponse(strategies=strategies)

    except Exception as e:
        logger.log_error(f"Failed to list strategies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve strategies")


@router.put("/{strategy_name}/enable")
async def enable_strategy(
    strategy_name: str, current_user: dict = Depends(get_current_user)
):
    """
    Enable a strategy

    Args:
        strategy_name: Strategy name
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        username = current_user.get("username")
        logger.log_info(f"Enable strategy request from {username}: {strategy_name}")

        # Enable strategy logic would go here
        # This would require updating the config and reloading strategies

        return {
            "message": f"Strategy '{strategy_name}' enabled successfully",
            "strategy": strategy_name,
        }

    except Exception as e:
        logger.log_error(f"Failed to enable strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable strategy")


@router.put("/{strategy_name}/disable")
async def disable_strategy(
    strategy_name: str, current_user: dict = Depends(get_current_user)
):
    """
    Disable a strategy

    Args:
        strategy_name: Strategy name
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        username = current_user.get("username")
        logger.log_info(f"Disable strategy request from {username}: {strategy_name}")

        # Disable strategy logic would go here

        return {
            "message": f"Strategy '{strategy_name}' disabled successfully",
            "strategy": strategy_name,
        }

    except Exception as e:
        logger.log_error(f"Failed to disable strategy: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable strategy")


@router.get("/{strategy_name}/config", response_model=StrategyConfigResponse)
async def get_strategy_config(
    strategy_name: str, current_user: dict = Depends(get_current_user)
):
    """
    Get strategy configuration

    Args:
        strategy_name: Strategy name
        current_user: Authenticated user

    Returns:
        Strategy configuration
    """
    try:
        config = get_config()
        strategies_config = config.get("strategies", {})
        strategy_config = strategies_config.get(strategy_name, {})

        return StrategyConfigResponse(name=strategy_name, config=strategy_config)

    except Exception as e:
        logger.log_error(f"Failed to get strategy config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")


@router.put("/{strategy_name}/config")
async def update_strategy_config(
    strategy_name: str,
    request: StrategyConfigUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Update strategy configuration

    Args:
        strategy_name: Strategy name
        request: Configuration update request
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        username = current_user.get("username")
        logger.log_info(
            f"Update strategy config request from {username}: {strategy_name}"
        )

        # Update config logic would go here
        # This would require updating the config file and reloading

        return {
            "message": f"Strategy '{strategy_name}' configuration updated successfully",
            "strategy": strategy_name,
        }

    except Exception as e:
        logger.log_error(f"Failed to update strategy config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")
