# FastAPI URL Shortener v2.0 - Quick Reference

## 📁 Project Structure

```
FastAPI/url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py              ⭐ UPDATED - Added middleware & background tasks
│   ├── models.py            ⭐ UPDATED - Added expiry & analytics
│   ├── schemas.py           ⭐ UPDATED - Added new schemas
│   ├── database.py          ⭐ UPDATED - Added Redis support
│   ├── services.py          ⭐ UPDATED - Major refactor with caching, hashing, analytics
│   ├── routes.py            ⭐ UPDATED - Added analytics endpoints & new features
│   ├── config.py            ✨ NEW - Configuration management
│   ├── middleware.py        ✨ NEW - Rate limiting middleware
│   ├── tasks.py             ✨ NEW - Background task scheduling
│   └── migrations/
│       ├── __init__.py
│       ├── 0001_initial.py
│       └── 0002_url_custom_code.py
├── tests/
│   ├── test_api.py
│   ├── test_api_final.py
│   └── TEST_REPORT.md
├── .env                     ⭐ UPDATED - Added Redis & settings
├── UPGRADE_GUIDE.md         ✨ NEW - Comprehensive upgrade guide
└── QUICK_REFERENCE.md       ✨ NEW - This file

```

## 🆕 New Files Created

### 1. **config.py** - Configuration Management
- Centralized settings from environment variables
- Pydantic BaseSettings for type validation
- Caching configuration defaults
- Rate limiting settings
- Analytics batch settings

### 2. **middleware.py** - Rate Limiting
- Per-IP rate limiting (sliding window)
- Minute and hour-level limits
- Redis-backed tracking
- Rate limit headers in responses
- Graceful degradation if Redis unavailable

### 3. **tasks.py** - Background Task Scheduler
- APScheduler integration
- Analytics processing task (every 5 minutes)
- Expired URL cleanup (every hour)
- Daily stats aggregation (every 24 hours)
- Startup/shutdown lifecycle management

## ⭐ Major Updates

### models.py
```python
# ADDED FIELDS:
- custom_code: Optional[str]           # User-provided custom codes
- expires_at: Optional[DateTime]       # URL expiry timestamp
- updated_at: DateTime                 # Modification timestamp

# NEW TABLE:
- Analytics model for tracking analytics data
  - click_data: JSON                   # hourly breakdown
  - referrer_data: JSON                # top referrers
  - device_data: JSON                  # device breakdown
```

### schemas.py
```python
# ENHANCED:
- URLCreate: Added custom_code and expires_in_days fields
- URLResponse: Added custom_code, expires_at, updated_at

# NEW SCHEMAS:
- AnalyticsData: Detailed analytics structure
- URLStats: Combined URL + Analytics response
- BulkURLResponse: Batch operations support
```

### database.py
```python
# ADDED:
- Redis connection and pool management
- get_redis() dependency injection
- Error handling and logging
- Graceful fallback for Redis unavailability
```

### services.py (Complete Rewrite)
```python
# NEW FUNCTIONS:
- hash_url()                    # SHA256 hashing
- validate_custom_code()        # Custom code validation
- cache_key()                   # Redis key generation
- get_cached_url()              # Retrieve from cache
- cache_url()                   # Store in cache
- invalidate_cache()            # Remove from cache
- is_url_expired()              # Check expiry
- process_analytics_batch()     # Batch analytics processing
- cleanup_expired_urls()        # Background cleanup task
- get_top_urls()               # Top URLs by clicks
- get_analytics()              # Analytics retrieval

# ENHANCED FUNCTIONS:
- create_short_url()            # Now supports custom codes & expiry
- increment_clicks()            # Now tracks analytics & device/referrer
- get_url_by_code()            # Now uses caching strategy
```

### routes.py (Complete Rewrite)
```python
# NEW ENDPOINTS:
POST  /shorten              # Create short URL (enhanced)
GET   /{short_code}         # Redirect (enhanced)
GET   /stats/{short_code}   # Analytics (NEW)
GET   /admin/stats          # Top URLs (NEW)
GET   /info/{short_code}    # URL info (NEW)
DELETE /{short_code}        # Deactivate URL (NEW)
GET   /                     # Root info (NEW)
GET   /health               # Health check (NEW)
GET   /config               # Config debug (NEW)
```

### main.py (Refactored)
```python
# ADDED:
- Lifespan context manager for startup/shutdown
- CORS middleware
- Rate limiting middleware
- Background task initialization
- Logging configuration
- Root endpoint with API info
```

### .env (Enhanced)
```
# NEW VARIABLES:
REDIS_URL=redis://localhost:6379/0
SHORT_CODE_LENGTH=6
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
CACHE_TTL_SECONDS=3600
ANALYTICS_BATCH_SIZE=100
ANALYTICS_FLUSH_INTERVAL=300
```

## 🔑 Key Implementation Details

### Caching (Cache-Aside Pattern)
1. Client requests `/abc123`
2. Check Redis for `url:abc123` → Cache hit → Return
3. Cache miss → Query PostgreSQL
4. Store in Redis with TTL
5. Return data to client

### Rate Limiting (Sliding Window)
```
Rate Limit Keys:
  rate_limit:minute:{ip}:{YYYY-MM-DD HH:MM}
  rate_limit:hour:{ip}:{YYYY-MM-DD HH}

Check per request:
  1. Get current minute count, check against RATE_LIMIT_PER_MINUTE
  2. Get current hour count, check against RATE_LIMIT_PER_HOUR
  3. Increment both if under limit
  4. Set Redis expiry for automatic reset
```

### Analytics Event Processing
```
Request Flow:
  Click → increment_clicks() → Queue event in Redis
  
Background Processing (every 5 minutes):
  1. Pop events from analytics_queue
  2. Batch process (max 100 events)
  3. Aggregate by hour
  4. Update device/referrer breakdown
  5. Commit to database
  6. Return processed count
```

### URL Expiry
```
Lifecycle:
  URL Created with expires_in_days=30
    ↓
  expires_at = now + 30 days
    ↓
  User accesses URL → Check if expired
    ↓
  If expired: Mark is_active=False, cache invalidate
    ↓
  Background cleanup (hourly) finds expired URLs
    ↓
  Clean up & optimize database
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd D:\CODING_HUB\SystemDesign
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
# Create/update .env with:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/url_shortener
REDIS_URL=redis://localhost:6379/0
```

### 3. Start Application
```bash
cd FastAPI/url-shortener
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test Endpoints
```bash
# Create short URL
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/long/url"}'

# Create with custom code & expiry
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/long/url",
    "custom_code": "mycode",
    "expires_in_days": 30
  }'

# Get analytics
curl http://localhost:8000/stats/mycode

# Redirect (follow redirects)
curl -L http://localhost:8000/mycode

# Check health
curl http://localhost:8000/health
```

## 📊 Database Indexes (Recommended)

```sql
CREATE INDEX idx_urls_expires_at ON urls(expires_at);
CREATE INDEX idx_urls_short_code ON urls(short_code);
CREATE INDEX idx_urls_custom_code ON urls(custom_code);
CREATE INDEX idx_analytics_url_id ON analytics(url_id);
CREATE INDEX idx_analytics_short_code ON analytics(short_code);
```

## 🔍 Monitoring

### Check Background Task Logs
- Look for: `"Processed N analytics events"`
- Look for: `"Cleaned up N expired URLs"`

### Monitor Redis
```bash
redis-cli
> KEYS url:*                    # See cached URLs
> LLEN analytics_queue          # Pending analytics events
> INFO stats                    # Redis statistics
```

### Monitor Database
```sql
-- Check analytics table
SELECT COUNT(*) FROM analytics;

-- Check active URLs
SELECT COUNT(*) FROM urls WHERE is_active = TRUE;

-- Check expired URLs
SELECT COUNT(*) FROM urls WHERE expires_at < NOW() AND is_active = TRUE;

-- Top URLs
SELECT short_code, clicks FROM urls ORDER BY clicks DESC LIMIT 10;
```

## ⚙️ Configuration Adjustments

```python
# In .env or config.py

# Increase cache lifetime
CACHE_TTL_SECONDS=7200          # 2 hours instead of 1

# Stricter rate limiting
RATE_LIMIT_PER_MINUTE=30        # 30 instead of 60
RATE_LIMIT_PER_HOUR=500         # 500 instead of 1000

# Faster analytics processing
ANALYTICS_BATCH_SIZE=500        # Process more events per cycle
ANALYTICS_FLUSH_INTERVAL=60     # Run every 1 minute instead of 5

# Longer short codes for more variety
SHORT_CODE_LENGTH=8             # 8 chars instead of 6
```

## 🚨 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Redis connection refused | Redis not running | Start Redis: `redis-server` |
| Rate limit too strict | Limits too low | Increase `RATE_LIMIT_*` in .env |
| No analytics data | Background task failed | Check logs for scheduler errors |
| Cache not working | Redis unavailable | App continues without cache (graceful degradation) |
| Expired URLs not cleaning | Scheduled task not running | Restart application |

## 📈 Version Info

- **Current Version**: 2.0.0
- **Release Date**: May 13, 2026
- **Python**: 3.12+
- **FastAPI**: 0.135.3+
- **SQLAlchemy**: 2.0.49+
- **Redis**: Python client 5.0.1+

---

For detailed documentation, see [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)
