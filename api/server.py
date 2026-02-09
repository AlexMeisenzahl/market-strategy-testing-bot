"""
Mobile Backend API Server

FastAPI-based REST API and WebSocket server for mobile trading bot control.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
import os
from datetime import datetime

from api.models.schemas import HealthResponse, ErrorResponse
from api.middleware.auth import get_current_user
from api.middleware.rate_limit import setup_rate_limiting
from logger import get_logger

# Global bot reference (will be set when server starts)
_bot_instance = None
_config = None


def set_bot_instance(bot, config):
    """Set the global bot instance"""
    global _bot_instance, _config
    _bot_instance = bot
    _config = config


def get_bot():
    """Get the bot instance"""
    if _bot_instance is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    return _bot_instance


def get_config():
    """Get the configuration"""
    if _config is None:
        raise HTTPException(status_code=503, detail="Configuration not loaded")
    return _config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    logger = get_logger()
    logger.log_info("Mobile API starting up...")
    yield
    logger.log_info("Mobile API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Polymarket Trading Bot API",
    description="Mobile Backend API for controlling the Polymarket trading bot",
    version="1.0.0",
    lifespan=lifespan,
)

# Get configuration from environment
api_config = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", 8000)),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
}

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup rate limiting
setup_rate_limiting(app)


# Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail, timestamp=datetime.now()).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger = get_logger()
    logger.log_error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error", detail=str(exc), timestamp=datetime.now()
        ).dict(),
    )


# Health check endpoint (no auth required)
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns the API health status and version information.
    """
    return HealthResponse(status="healthy", timestamp=datetime.now(), version="1.0.0")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Polymarket Trading Bot API",
        "version": "1.0.0",
        "status": "running",
    }


# Import and include routers (these will be created next)
try:
    from api.routes.auth import router as auth_router

    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
except ImportError:
    pass

try:
    from api.routes.markets import router as markets_router

    app.include_router(markets_router, prefix="/api/markets", tags=["Markets"])
except ImportError:
    pass

try:
    from api.routes.trades import router as trades_router

    app.include_router(trades_router, prefix="/api/trade", tags=["Trading"])
except ImportError:
    pass

try:
    from api.routes.positions import router as positions_router

    app.include_router(positions_router, prefix="/api/positions", tags=["Positions"])
except ImportError:
    pass

try:
    from api.routes.strategies import router as strategies_router

    app.include_router(strategies_router, prefix="/api/strategies", tags=["Strategies"])
except ImportError:
    pass

try:
    from api.websocket.manager import websocket_endpoint

    app.add_websocket_route("/ws/stream", websocket_endpoint)
except ImportError:
    pass


def run_server(bot, config):
    """
    Run the API server

    Args:
        bot: Bot instance
        config: Configuration dictionary
    """
    import uvicorn

    # Set global bot instance
    set_bot_instance(bot, config)

    # Get API configuration
    mobile_api_config = config.get("mobile_api", {})
    host = mobile_api_config.get("host", "0.0.0.0")
    port = mobile_api_config.get("port", 8000)

    logger = get_logger()
    logger.log_info(f"Starting Mobile API server on {host}:{port}")

    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    # For development/testing
    from config.config_loader import get_config

    config_loader = get_config()
    config = config_loader.get_all()
    run_server(None, config)
