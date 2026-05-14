"""
Enhanced URL Shortener routes with analytics, caching, and rate limiting
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from . import models, schemas, services
from .database import get_db
from .config import get_settings

router = APIRouter()
settings = get_settings()

# ==================== CORE SHORTENER ENDPOINTS ====================

@router.post("/shorten", response_model=schemas.URLResponse, tags=["URL Shortener"])
def shorten_url(
    url_data: schemas.URLCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new short URL
    
    Features:
    - Custom short codes (optional)
    - URL expiry support (1-365 days)
    - Automatic caching with Redis
    - Analytics tracking initialization
    
    Example:
    ```json
    {
        "original_url": "https://example.com/very/long/url",
        "custom_code": "myurl",
        "expires_in_days": 30
    }
    ```
    """
    try:
        url = services.create_short_url(db=db, url_data=url_data)
        return url
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{short_code}", tags=["URL Shortener"])
def redirect_url(
    short_code: str,
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None),
    referer: Optional[str] = Header(None)
):
    """
    Redirect to original URL using short code
    
    Features:
    - Cached lookups for performance
    - Automatic expiry checking
    - Click tracking and analytics
    - Device and referrer tracking
    """
    
    url = services.get_url_by_code(db=db, short_code=short_code)
    
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found or expired")
    
    # Increment clicks and track analytics
    device = "mobile" if "mobile" in (user_agent or "").lower() else "desktop"
    services.increment_clicks(
        db=db,
        url=url,
        referrer=referer or "direct",
        device=device
    )
    
    # Redirect with cache headers
    response = RedirectResponse(url=url.original_url, status_code=301)
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    return response


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/stats/{short_code}", response_model=schemas.AnalyticsData, tags=["Analytics"])
def get_stats(
    short_code: str,
    db: Session = Depends(get_db)
):
    """
    Get analytics and statistics for a short URL
    
    Returns:
    - Total clicks
    - Unique visitors
    - Click distribution (hourly/daily)
    - Top referrers
    - Device breakdown
    """
    
    analytics = services.get_analytics(db=db, short_code=short_code)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="No analytics found for this URL")
    
    return analytics


@router.get("/admin/stats", response_model=List[schemas.URLResponse], tags=["Admin"])
def get_top_urls(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get top URLs by click count
    
    Parameters:
    - limit: Number of URLs to return (1-100)
    """
    
    urls = services.get_top_urls(db=db, limit=limit)
    return urls


# ==================== URL MANAGEMENT ENDPOINTS ====================

@router.get("/info/{short_code}", response_model=schemas.URLResponse, tags=["URL Info"])
def get_url_info(
    short_code: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a short URL"""
    
    url = services.get_url_by_code(db=db, short_code=short_code)
    
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return url


@router.delete("/{short_code}", tags=["URL Management"])
def deactivate_url(
    short_code: str,
    db: Session = Depends(get_db)
):
    """
    Deactivate/delete a short URL (soft delete)
    
    The URL will not redirect anymore but remains in database for analytics
    """
    
    url = services.deactivate_url(db=db, short_code=short_code)
    
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return {"message": f"URL {short_code} has been deactivated"}


# ==================== HEALTH & DEBUG ENDPOINTS ====================

@router.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.app_version}


@router.get("/config", tags=["Debug"])
def get_config():
    """Get current configuration (debug only)"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "short_code_length": settings.short_code_length,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "cache_ttl_seconds": settings.cache_ttl_seconds,
        "analytics_batch_size": settings.analytics_batch_size
    }


"""
CONCEPTS IMPLEMENTED:

1. HASHING (SHA256)
   - Used for URL verification and consistency
   - Implemented in services.hash_url()

2. TTL (Time To Live)
   - URL expiry support (1-365 days configurable)
   - Redis cache TTL set to 1 hour (configurable)
   - Analytics data TTL set to 24 hours
   - Automatic cleanup of expired URLs via background task

3. CACHING STRATEGY
   - Redis for distributed caching
   - Cache-aside pattern (check cache before DB)
   - Automatic invalidation on updates
   - Graceful fallback when Redis unavailable
   - Cache keys: url:{short_code}

4. ASYNC TASKS
   - Analytics event queuing in Redis
   - Batch processing of events (every 5 minutes)
   - Hourly expired URL cleanup
   - Daily stats aggregation
   - APScheduler for reliable scheduling

5. RATE LIMITING
   - Per-IP rate limiting (60 req/min, 1000 req/hour)
   - Sliding window implementation with Redis
   - Middleware-based enforcement
   - HTTP 429 status for exceeded limits

6. ANALYTICS
   - Click counting and tracking
   - Device type detection (mobile/desktop)
   - Referrer source tracking
   - Hourly click distribution
   - Top referrers and device breakdown
   - Background batch processing

7. CUSTOM CODES
   - User-provided custom short codes
   - Validation (3-20 chars, alphanumeric)
   - Uniqueness checking
   - Optional support (auto-generate if not provided)

"""



