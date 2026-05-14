"""
Rate limiting middleware using Redis
Implements sliding window rate limiting per IP address
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
import logging
from .database import get_redis, redis_client
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that tracks requests per IP
    - Per minute limit (e.g., 60 requests/min)
    - Per hour limit (e.g., 1000 requests/hour)
    """
    
    async def dispatch(self, request: Request, call_next):
        
        if not redis_client:
            # If Redis is not available, skip rate limiting
            return await call_next(request)
        
        # Skip rate limiting for certain paths
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            # Check minute limit
            minute_key = f"rate_limit:minute:{client_ip}:{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            minute_count = int(redis_client.get(minute_key) or 0)
            
            if minute_count >= settings.rate_limit_per_minute:
                logger.warning(f"Rate limit exceeded (per minute) for IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests per minute"
                )
            
            # Check hour limit
            hour_key = f"rate_limit:hour:{client_ip}:{datetime.utcnow().strftime('%Y-%m-%d %H')}"
            hour_count = int(redis_client.get(hour_key) or 0)
            
            if hour_count >= settings.rate_limit_per_hour:
                logger.warning(f"Rate limit exceeded (per hour) for IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {settings.rate_limit_per_hour} requests per hour"
                )
            
            # Increment counters
            redis_client.incr(minute_key)
            redis_client.expire(minute_key, 60)  # Reset after 1 minute
            
            redis_client.incr(hour_key)
            redis_client.expire(hour_key, 3600)  # Reset after 1 hour
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue processing if rate limiting fails
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(settings.rate_limit_per_minute - minute_count)
        response.headers["X-RateLimit-Reset"] = str(int((datetime.utcnow() + timedelta(minutes=1)).timestamp()))
        
        return response
