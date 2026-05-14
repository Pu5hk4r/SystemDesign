'''
routes.py — sirf request lo, response do. Koi logic nahi.

services.py — asli kaam yahan. Short code generate karna, 
URL save karna, clicks count karna — sab yahan.

Route  →  Service  →  Database
(request)  (logic)   (data)
'''

import random
import string
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from .database import get_redis, redis_client
from .config import get_settings

settings = get_settings()

# ==================== HASHING & CODE GENERATION ====================

def hash_url(url: str, salt: Optional[str] = None) -> str:
    """Generate a hash of URL using SHA256 for consistency"""
    if salt is None:
        salt = settings.hash_salt
    
    combined = f"{url}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()


def generate_short_code(length: Optional[int] = None) -> str:
    """
    Generate random short code
    length: number of characters (default from settings)
    """
    if length is None:
        length = settings.short_code_length
    
    charset = settings.short_code_charset
    return "".join(random.choices(charset, k=length))


def validate_custom_code(code: str, db: Session) -> bool:
    """
    Validate if custom code is available (alphanumeric, 3-20 chars, unique)
    """
    if not (3 <= len(code) <= 20):
        return False
    
    if not code.replace("_", "").replace("-", "").isalnum():
        return False
    
    # Check if code already exists in database
    existing = db.query(models.URL).filter(
        models.URL.short_code == code
    ).first()
    
    return existing is None


# ==================== CACHING STRATEGY ====================

def cache_key(code: str, prefix: str = "url") -> str:
    """Generate cache key for Redis"""
    return f"{prefix}:{code}"


def get_cached_url(short_code: str) -> Optional[dict]:
    """Get URL from Redis cache"""
    if not redis_client:
        return None
    
    try:
        key = cache_key(short_code)
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print(f"Cache read error: {e}")
        return None


def cache_url(url: models.URL, ttl: Optional[int] = None) -> None:
    """Store URL in Redis cache with TTL"""
    if not redis_client:
        return
    
    if ttl is None:
        ttl = settings.cache_ttl_seconds
    
    try:
        key = cache_key(url.short_code)
        data = {
            "id": url.id,
            "original_url": url.original_url,
            "short_code": url.short_code,
            "custom_code": url.custom_code,
            "is_active": url.is_active,
            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
        }
        redis_client.setex(key, ttl, json.dumps(data))
    except Exception as e:
        print(f"Cache write error: {e}")


def invalidate_cache(short_code: str) -> None:
    """Remove URL from cache"""
    if not redis_client:
        return
    
    try:
        key = cache_key(short_code)
        redis_client.delete(key)
    except Exception as e:
        print(f"Cache invalidate error: {e}")


# ==================== URL MANAGEMENT ====================

def is_url_expired(url: models.URL) -> bool:
    """Check if URL has expired"""
    if url.expires_at is None:
        return False
    
    return datetime.utcnow() > url.expires_at


def create_short_url(db: Session, url_data: schemas.URLCreate) -> models.URL:
    """
    Create a new short URL with optional custom code and expiry
    - Generates unique short code
    - Supports custom codes
    - Implements TTL (expiry)
    - Caches the URL in Redis
    """
    
    # Determine short code
    if url_data.custom_code:
        # Validate and use custom code
        if not validate_custom_code(url_data.custom_code, db):
            raise ValueError("Custom code is invalid or already exists")
        short_code = url_data.custom_code
    else:
        # Generate random code ensuring uniqueness
        while True:
            short_code = generate_short_code()
            existing = db.query(models.URL).filter(
                models.URL.short_code == short_code
            ).first()
            if not existing:
                break
    
    # Calculate expiry date
    expires_at = None
    if url_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=url_data.expires_in_days)
    
    # Create URL record
    db_url = models.URL(
        original_url=str(url_data.original_url),
        short_code=short_code,
        custom_code=url_data.custom_code,
        expires_at=expires_at
    )
    
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    # Cache in Redis
    cache_url(db_url)
    
    # Initialize analytics
    _initialize_analytics(db, db_url)
    
    return db_url


def get_url_by_code(db: Session, short_code: str) -> Optional[models.URL]:
    """
    Get URL by short code with caching strategy
    - First check Redis cache
    - Fall back to database
    - Update cache on hit
    """
    
    # Try cache first
    cached = get_cached_url(short_code)
    if cached:
        # Reconstruct URL object from cache (for validation)
        pass
    
    # Query database
    url = db.query(models.URL).filter(
        models.URL.short_code == short_code,
        models.URL.is_active == True
    ).first()
    
    # Check expiry
    if url and is_url_expired(url):
        # Mark as inactive
        url.is_active = False
        db.commit()
        invalidate_cache(short_code)
        return None
    
    # Update cache
    if url:
        cache_url(url)
    
    return url


def increment_clicks(db: Session, url: models.URL, referrer: Optional[str] = None, device: Optional[str] = None) -> models.URL:
    """
    Increment click count and store analytics
    - Update main URL clicks counter
    - Store in analytics for aggregation
    - Track in Redis for rate limiting
    """
    
    url.clicks += 1
    db.commit()
    db.refresh(url)
    
    # Invalidate cache to ensure fresh data
    invalidate_cache(url.short_code)
    
    # Queue analytics event
    _queue_analytics_event(db, url, referrer, device)
    
    return url


def deactivate_url(db: Session, short_code: str) -> models.URL:
    """Deactivate a URL (soft delete)"""
    
    url = db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()
    
    if url:
        url.is_active = False
        db.commit()
        db.refresh(url)
        invalidate_cache(short_code)
    
    return url


# ==================== ANALYTICS ====================

def _initialize_analytics(db: Session, url: models.URL) -> models.Analytics:
    """Initialize analytics record for new URL"""
    
    analytics = models.Analytics(
        url_id=url.id,
        short_code=url.short_code,
        clicks_count=0,
        unique_visitors=0,
        click_data={},
        referrer_data={},
        device_data={}
    )
    
    db.add(analytics)
    db.commit()
    return analytics


def _queue_analytics_event(db: Session, url: models.URL, referrer: Optional[str] = None, device: Optional[str] = None) -> None:
    """
    Queue analytics event to Redis for batch processing
    This implements the background task concept
    """
    
    if not redis_client:
        return
    
    try:
        event = {
            "url_id": url.id,
            "short_code": url.short_code,
            "timestamp": datetime.utcnow().isoformat(),
            "referrer": referrer or "direct",
            "device": device or "unknown"
        }
        
        # Queue in Redis list for batch processing
        redis_client.lpush(f"analytics_queue", json.dumps(event))
        
        # Set TTL for event queue
        redis_client.expire(f"analytics_queue", 86400)
    except Exception as e:
        print(f"Analytics queue error: {e}")


def get_analytics(db: Session, short_code: str) -> Optional[schemas.AnalyticsData]:
    """Retrieve analytics for a URL"""
    
    url = db.query(models.URL).filter(
        models.URL.short_code == short_code
    ).first()
    
    if not url:
        return None
    
    # Get analytics record
    analytics = db.query(models.Analytics).filter(
        models.Analytics.url_id == url.id
    ).order_by(models.Analytics.timestamp.desc()).first()
    
    if not analytics:
        return None
    
    return schemas.AnalyticsData(
        url_id=url.id,
        short_code=url.short_code,
        total_clicks=url.clicks,
        unique_visitors=analytics.unique_visitors,
        click_distribution=analytics.click_data or {},
        top_referrers=analytics.referrer_data or {},
        device_breakdown=analytics.device_data or {},
        created_at=url.created_at,
        last_accessed=analytics.timestamp
    )


def process_analytics_batch(db: Session) -> int:
    """
    Background task: Process queued analytics events in batch
    - Read from Redis queue
    - Aggregate data
    - Store in database
    - Returns count of processed events
    """
    
    if not redis_client:
        return 0
    
    processed = 0
    batch_size = settings.analytics_batch_size
    
    try:
        # Get batch of events from queue
        for _ in range(batch_size):
            event_json = redis_client.rpop("analytics_queue")
            
            if not event_json:
                break
            
            event = json.loads(event_json)
            short_code = event.get("short_code")
            referrer = event.get("referrer", "direct")
            device = event.get("device", "unknown")
            
            # Update analytics
            analytics = db.query(models.Analytics).filter(
                models.Analytics.short_code == short_code
            ).first()
            
            if analytics:
                # Update click distribution
                now = datetime.utcnow()
                hour_key = now.strftime("%Y-%m-%d %H:00")
                
                if not analytics.click_data:
                    analytics.click_data = {}
                
                analytics.click_data[hour_key] = analytics.click_data.get(hour_key, 0) + 1
                
                # Update referrer data
                if not analytics.referrer_data:
                    analytics.referrer_data = {}
                
                analytics.referrer_data[referrer] = analytics.referrer_data.get(referrer, 0) + 1
                
                # Update device data
                if not analytics.device_data:
                    analytics.device_data = {}
                
                analytics.device_data[device] = analytics.device_data.get(device, 0) + 1
                
                analytics.unique_visitors += 1
                analytics.timestamp = now
                
                db.commit()
                processed += 1
        
        return processed
    
    except Exception as e:
        print(f"Analytics batch processing error: {e}")
        return processed


def get_top_urls(db: Session, limit: int = 10) -> list:
    """Get top URLs by click count"""
    
    return db.query(models.URL).filter(
        models.URL.is_active == True
    ).order_by(models.URL.clicks.desc()).limit(limit).all()


def cleanup_expired_urls(db: Session) -> int:
    """
    Background task: Cleanup expired URLs
    - Mark expired URLs as inactive
    - Clear from cache
    - Returns count of expired URLs
    """
    
    now = datetime.utcnow()
    
    # Find expired URLs
    expired_urls = db.query(models.URL).filter(
        models.URL.expires_at <= now,
        models.URL.is_active == True
    ).all()
    
    count = 0
    for url in expired_urls:
        url.is_active = False
        invalidate_cache(url.short_code)
        count += 1
    
    if expired_urls:
        db.commit()
    
    return count





'''
Line by line samajh:
generate_short_code — ascii_letters matlab a-z, A-Z. digits matlab 0-9. 
random.choices 6 random characters pick karta hai. join se string banta hai.

while True — loop isliye kyunki agar generated code pehle se exist kare toh naya banao. 
Collision handle karna zaroori hai.

db.add → db.commit → db.refresh — ye teen steps hamesha saath aate hain.
 Add karo, save karo, latest data wapas lo.

get_url_by_code — is_active == True filter isliye ki band URLs pe redirect na ho.
increment_clicks — har redirect pe clicks +1 hoga.
'''

'''
Function 1:
def generate_short_code(length=6):
Sirf ek parameter — length=6
length — kitne characters ka code banana hai. =6 matlab default value — agar tu kuch na de toh 6 leta hai automatically.
pythongenerate_short_code()    # 6 characters
generate_short_code(8)   # 8 characters


Function 2:
pythondef create_short_url(db: Session, url_data: schemas.URLCreate):
db: Session — database connection chahiye. Bina iske database mein save kaise karenge? Route se aata hai via get_db().
url_data: schemas.URLCreate — user ne jo URL bheja wo yahan aata hai. URLCreate schema yaad hai? Usme original_url tha — wahi yahan milta hai url_data.original_url se.

Function 3:
pythondef get_url_by_code(db: Session, short_code: str):
db: Session — database mein dhundhna hai toh connection chahiye.
short_code: str — kaunsa code dhundhna hai? User ne /abc123 hit kiya toh abc123 yahan aayega.

Function 4:
pythondef increment_clicks(db: Session, url: models.URL):
db: Session — clicks save karne ke liye connection chahiye.
url: models.URL — pehle se mila hua URL object. Naya dhundhne ki zaroorat nahi — pehle get_url_by_code se mila, wahi yahan pass kiya.

Ek pattern notice kar:
db: Session    →  hamesha jab database se kaam ho
str, int       →  simple values jab user se aaye
schemas.X      →  jab poora request object aaye
models.X       →  jab database object aaye

Flow samajh:
User request aai
    ↓
Route ne pakdi
    ↓
Service ko di (db + data)
    ↓
Service ne database se kaam kiya
    ↓
Result wapas route ko
    ↓
User ko response
'''