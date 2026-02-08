"""
Security Middleware and Utilities
JWT Authentication, Rate Limiting, CORS, Security Headers
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any, Callable
from flask import request, jsonify, g
import logging


class JWTAuth:
    """JWT Authentication system"""
    
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.algorithm = 'HS256'
        self.expiration_hours = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
        self.logger = logging.getLogger(__name__)
    
    def generate_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.expiration_hours),
            'iat': datetime.utcnow(),
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid token")
            return None
    
    def require_auth(self, f: Callable) -> Callable:
        """Decorator to require JWT authentication"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                parts = auth_header.split()
                if len(parts) == 2 and parts[0] == 'Bearer':
                    token = parts[1]
            
            # Get token from query parameter (fallback)
            if not token and 'token' in request.args:
                token = request.args.get('token')
            
            if not token:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Verify token
            payload = self.verify_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Store user info in request context
            g.user_id = payload.get('user_id')
            g.token_payload = payload
            
            return f(*args, **kwargs)
        
        return decorated


class APIKeyAuth:
    """API Key authentication"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.logger = logging.getLogger(__name__)
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from environment or config"""
        # For now, load from environment
        keys = {}
        
        # Master API key
        master_key = os.getenv('MASTER_API_KEY')
        if master_key:
            keys[master_key] = {
                'name': 'Master Key',
                'permissions': ['read', 'write', 'admin'],
                'created_at': datetime.utcnow().isoformat()
            }
        
        return keys
    
    def generate_key(self, name: str, permissions: list) -> str:
        """Generate new API key"""
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = {
            'name': name,
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat()
        }
        return api_key
    
    def verify_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key"""
        return self.api_keys.get(api_key)
    
    def require_api_key(self, required_permission: Optional[str] = None) -> Callable:
        """Decorator to require API key"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated(*args, **kwargs):
                api_key = None
                
                # Get from header
                if 'X-API-Key' in request.headers:
                    api_key = request.headers['X-API-Key']
                
                # Get from query
                if not api_key and 'api_key' in request.args:
                    api_key = request.args.get('api_key')
                
                if not api_key:
                    return jsonify({'error': 'API key required'}), 401
                
                # Verify key
                key_info = self.verify_key(api_key)
                if not key_info:
                    return jsonify({'error': 'Invalid API key'}), 401
                
                # Check permissions
                if required_permission:
                    if required_permission not in key_info.get('permissions', []):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                
                g.api_key_info = key_info
                
                return f(*args, **kwargs)
            
            return decorated
        return decorator


class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        # Prevent XSS
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HTTPS enforcement
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:;"
        )
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}  # {client_id: [(timestamp, count)]}
        self.logger = logging.getLogger(__name__)
    
    def is_allowed(self, client_id: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                (ts, count) for ts, count in self.requests[client_id]
                if ts > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Count requests in window
        total_requests = sum(count for _, count in self.requests[client_id])
        
        if total_requests >= max_requests:
            self.logger.warning(f"Rate limit exceeded for {client_id}")
            return False
        
        # Add new request
        self.requests[client_id].append((now, 1))
        return True
    
    def rate_limit(self, max_requests: int = 100, window_seconds: int = 3600) -> Callable:
        """Decorator for rate limiting"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated(*args, **kwargs):
                # Use IP address as client ID
                client_id = request.remote_addr or 'unknown'
                
                if not self.is_allowed(client_id, max_requests, window_seconds):
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                
                return f(*args, **kwargs)
            
            return decorated
        return decorator


# Global instances
jwt_auth = JWTAuth()
api_key_auth = APIKeyAuth()
rate_limiter = RateLimiter()
security_headers = SecurityHeaders()
