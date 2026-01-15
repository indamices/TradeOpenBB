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
        # #region agent log
        with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"middleware.py:34","message":"RateLimitMiddleware dispatch entry","data":{"path":request.url.path,"method":request.method,"origin":request.headers.get("origin"),"client_ip":request.client.host if request.client else "unknown"}})+'\n')
        # #endregion
        
        # Skip rate limiting for health checks and OPTIONS requests
        if request.url.path == "/" or request.url.path == "/health" or request.method == "OPTIONS":
            # #region agent log
            with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"middleware.py:40","message":"Skipping rate limit","data":{"path":request.url.path,"method":request.method}})+'\n')
            # #endregion
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
            # #region agent log
            with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"middleware.py:60","message":"Rate limit exceeded - creating response without CORS","data":{"path":request.url.path,"client_ip":client_ip,"requests_count":len(rate_limit_storage[client_ip])}})+'\n')
            # #endregion
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."
                }
            )
            # Add CORS headers to rate limit response
            origin = request.headers.get("origin")
            if origin:
                allowed_origins = ["http://localhost:3000", "http://localhost:5173", "https://tradeopenbb-frontend.onrender.com"]
                import re
                origin_pattern = re.compile(r"https://.*\.render\.com|https://.*\.railway\.app|https://.*\.fly\.dev|https://.*\.vercel\.app")
                if origin in allowed_origins or origin_pattern.match(origin):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = "*"
                    response.headers["Access-Control-Allow-Headers"] = "*"
            # #region agent log
            with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"middleware.py:77","message":"Rate limit response with CORS headers","data":{"origin":origin,"cors_added":origin in allowed_origins or (origin and origin_pattern.match(origin)) if origin else False}})+'\n')
            # #endregion
            return response
        
        # Add current request
        rate_limit_storage[client_ip].append((current_time, request.url.path))
        
        # Process request
        response = await call_next(request)
        
        # #region agent log
        with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"middleware.py:90","message":"Response after call_next","data":{"path":request.url.path,"status_code":response.status_code if hasattr(response,'status_code') else None,"cors_headers":{k:v for k,v in response.headers.items() if 'access-control' in k.lower()}}})+'\n')
        # #endregion
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
