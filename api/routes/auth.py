"""
Authentication Routes

Handles user authentication, login, logout, and token management.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta

from api.models.schemas import LoginRequest, TokenResponse, RefreshTokenRequest
from api.middleware.auth import (
    create_access_token, 
    verify_password, 
    get_current_user,
    JWT_EXPIRATION_HOURS
)
from logger import get_logger

router = APIRouter()
logger = get_logger()

# Hardcoded user for simplicity (in production, use a database)
# Default credentials: admin / admin123
# WARNING: Change these credentials immediately in production!
# TODO: Implement proper user database and require password change on first login
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqLWzBdCZK",  # admin123
        "email": "admin@example.com",
        "require_password_change": True  # Flag for password change requirement
    }
}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    User login endpoint
    
    Authenticates user and returns JWT access token.
    
    Args:
        request: Login credentials
        
    Returns:
        JWT token and expiration info
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get user from database
    user = USERS_DB.get(request.username)
    
    if not user:
        logger.log_warning(f"Login attempt for non-existent user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        logger.log_warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(hours=JWT_EXPIRATION_HOURS)
    )
    
    logger.log_info(f"User logged in: {request.username}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    User logout endpoint
    
    Logs out the current user (token invalidation handled client-side).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    username = current_user.get("username")
    logger.log_info(f"User logged out: {username}")
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh JWT token endpoint
    
    Issues a new JWT token (simplified implementation).
    
    Args:
        request: Refresh token request
        
    Returns:
        New JWT token
    """
    # In a full implementation, verify the refresh token
    # For simplicity, we'll just issue a new token
    # In production, implement proper refresh token validation
    
    try:
        from api.middleware.auth import verify_token
        
        # Verify the provided token
        payload = verify_token(request.refresh_token)
        username = payload.get("sub")
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(hours=JWT_EXPIRATION_HOURS)
        )
        
        logger.log_info(f"Token refreshed for user: {username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600
        )
        
    except Exception as e:
        logger.log_error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
