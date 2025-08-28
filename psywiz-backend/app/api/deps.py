"""
API-specific dependencies and middleware.
"""

import time
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.config import settings


# Optional API authentication (if needed in the future)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user from API token (placeholder for future authentication).
    
    Currently returns None (no authentication required).
    This can be expanded to support JWT tokens, API keys, etc.
    """
    # For now, no authentication is required
    # This can be implemented later if needed
    return None


def require_api_key(
    api_key: Optional[str] = None
) -> bool:
    """
    Require API key for certain endpoints (placeholder).
    
    Args:
        api_key: API key from header or query parameter
        
    Returns:
        True if valid (currently always True)
    """
    # Placeholder for API key validation
    # Can be implemented if API key authentication is needed
    return True


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Check if under limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


async def check_rate_limit(request: Request) -> None:
    """
    Check rate limiting for requests.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    # Get client identifier (IP address)
    client_ip = request.client.host if request.client else "unknown"
    
    # Check if request forwarded through proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for client: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )


async def log_request_info(request: Request) -> dict:
    """
    Log and return request information.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with request information
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client_ip": client_ip,
        "user_agent": user_agent,
        "timestamp": time.time()
    }
    
    return request_info


def validate_content_type(
    request: Request,
    expected_type: str = "application/json"
) -> bool:
    """
    Validate request content type.
    
    Args:
        request: FastAPI request object
        expected_type: Expected content type
        
    Returns:
        True if valid content type
        
    Raises:
        HTTPException: If invalid content type
    """
    content_type = request.headers.get("Content-Type", "")
    
    if not content_type.startswith(expected_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content-Type must be {expected_type}"
        )
    
    return True


async def get_request_size(request: Request) -> int:
    """
    Get request body size.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request body size in bytes
    """
    content_length = request.headers.get("Content-Length")
    
    if content_length:
        return int(content_length)
    
    return 0


def validate_request_size(
    max_size_mb: int = 10
) -> callable:
    """
    Create a dependency to validate request size.
    
    Args:
        max_size_mb: Maximum request size in MB
        
    Returns:
        Dependency function
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    async def _validate_size(request: Request) -> None:
        size = await get_request_size(request)
        
        if size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Maximum size: {max_size_mb}MB"
            )
    
    return _validate_size


# Common dependencies that can be used across endpoints
CommonDeps = {
    "rate_limit": check_rate_limit,
    "request_info": log_request_info,
    "validate_json": lambda req: validate_content_type(req, "application/json"),
    "validate_size_10mb": validate_request_size(10),
    "validate_size_100mb": validate_request_size(100),
}