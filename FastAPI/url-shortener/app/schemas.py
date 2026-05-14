'''
schemas.py — ye samajh pehle.
Model vs Schema fark:

Model = database table
Schema = API request/response ka format — user kya bhejega, user ko kya milega

Soch — URL shortener mein:
User kya bhejega? → sirf original_url
User ko kya milega? → short_code, original_url, clicks, created_at

Samajh:
URLCreate — user sirf URL bhejega. HttpUrl automatically check karega valid URL hai ya nahi. google nahi chalega, 
https://google.com chalega.

URLResponse — user ko ye sab milega response mein.

class Config: from_attributes = True — ye SQLAlchemy model ko Pydantic schema 
mein convert karne ke liye chahiye. 

Bina iske response nahi banega.

Ek important cheez notice kar:

URLCreate mein HttpUrl hai — strict validation.

URLResponse mein str hai — kyunki database se aata hai toh 
already valid hai, strict validation ki zaroorat nahi.

'''
#HttpUrl — automatically validate karta hai ki valid URL hai ya nahi. Koi random string nahi chalegi.

from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

#User se input lega -- sirf original URL aur optional expiry/custom code

class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_code: Optional[str] = Field(None, min_length=3, max_length=20, description="Custom short code")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="URL expiry in days (1-365)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_url": "https://www.example.com/very/long/url",
                "custom_code": "myurl",
                "expires_in_days": 30
            }
        }


# User ko response denge -- saari details

class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    custom_code: Optional[str]
    clicks: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalyticsData(BaseModel):
    """Analytics summary for a short URL"""
    url_id: int
    short_code: str
    total_clicks: int
    unique_visitors: int
    click_distribution: Dict[str, int]  # hourly or daily breakdown
    top_referrers: Dict[str, int]
    device_breakdown: Dict[str, int]
    created_at: datetime
    last_accessed: Optional[datetime]
    
    class Config:
        from_attributes = True


class URLStats(BaseModel):
    """Detailed stats for a URL"""
    url: URLResponse
    analytics: AnalyticsData


class BulkURLResponse(BaseModel):
    """Response for bulk URL creation"""
    total: int
    successful: int
    failed: int
    urls: list[URLResponse]

    class Config:
        from_attributes = True
