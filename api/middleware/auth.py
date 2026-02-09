"""
Authentication Middleware

JWT-based authentication for API endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

from logger import get_logger

# Security scheme
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv('API_JWT_SECRET', 'change-this-secret-key')

# Security check - fail if using default secret
if JWT_SECRET == 'change-this-secret-key':
    logger.log_error("CRITICAL: Using default JWT secret! Set API_JWT_SECRET in .env file.")
    # In production, you may want to raise an exception here:
    # raise ValueError("JWT secret must be changed from default value")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

logger = get_logger()


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict:
    """
    Verify a JWT token
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.log_error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Get the current authenticated user
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"username": username, "payload": payload}


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    """
    Get the current user if authenticated, None otherwise
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        User data from token or None
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches
    """
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)
