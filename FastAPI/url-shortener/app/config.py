"""
Configuration settings for URL Shortener
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Application
    app_name: str = "URL Shortener with Analytics"
    app_version: str = "2.0.0"
    
    # Short code settings
    short_code_length: int = 6
    short_code_charset: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    # Rate limiting
    rate_limit_per_minute: int = 60  # Per IP
    rate_limit_per_hour: int = 1000
    
    # Caching
    cache_ttl_seconds: int = 3600  # 1 hour default
    cache_analytics_ttl: int = 86400  # 24 hours for analytics
    
    # Analytics
    analytics_batch_size: int = 100
    analytics_flush_interval: int = 300  # 5 minutes
    
    # URL Expiry
    default_expiry_days: int = 365
    max_expiry_days: int = 3650  # 10 years
    
    # Hashing
    hash_salt: str = "url_shortener_salt_2024"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
