"""
Middleware for rate limiting and request optimization
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Rate limiting storage: {client_ip: [(timestamp, endpoint), ...]}
rate_limit_storage: Dict[str, list] = defaultdict(list)

# Request cache for market data (5 second TTL)
market_data_cache = TTLCache(maxsize=1000, ttl=5)

# Request deduplication: {request_key: (timestamp, response)}
request_dedup: Dict[str, Tuple[float, dict]] = {}
DEDUP_TTL = 2  # 2 seconds

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent request overload"""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/" or request.url.path == "/health":
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old entries
        current_time = time.time()
        rate_limit_storage[client_ip] = [
            (ts, endpoint) for ts, endpoint in rate_limit_storage[client_ip]
            if current_time - ts < self.window_seconds
        ]
        
        # Check rate limit
        if len(rate_limit_storage[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."
                }
            )
        
        # Add current request
        rate_limit_storage[client_ip].append((current_time, request.url.path))
        
        # Process request
        response = await call_next(request)
        return response

def get_cache_key(request: Request) -> str:
    """Generate cache key from request"""
    return f"{request.method}:{request.url.path}:{str(request.query_params)}"

def check_request_dedup(request: Request) -> dict:
    """Check if this is a duplicate request within TTL"""
    cache_key = get_cache_key(request)
    current_time = time.time()
    
    if cache_key in request_dedup:
        timestamp, response = request_dedup[cache_key]
        if current_time - timestamp < DEDUP_TTL:
            return response
    
    return None

def store_request_dedup(request: Request, response: dict):
    """Store request response for deduplication"""
    cache_key = get_cache_key(request)
    current_time = time.time()
    
    # Clean old entries
    keys_to_remove = [
        key for key, (ts, _) in request_dedup.items()
        if current_time - ts >= DEDUP_TTL
    ]
    for key in keys_to_remove:
        request_dedup.pop(key, None)
    
    request_dedup[cache_key] = (current_time, response)
