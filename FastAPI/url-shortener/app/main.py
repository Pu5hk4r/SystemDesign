"""
FastAPI URL Shortener with Analytics
Features: Custom codes, Expiry, Click tracking, Redis caching, PostgreSQL, Background tasks
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import router
from .middleware import RateLimitMiddleware
from .tasks import start_background_tasks, stop_background_tasks
from .config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# ==================== LIFECYCLE EVENTS ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app
    - Initialize database tables
    - Start background scheduler tasks
    - Clean up on shutdown
    """
    
    # Startup
    logger.info("🚀 Starting URL Shortener application...")
    
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created/verified")
    
    # Start background tasks
    start_background_tasks()
    logger.info("✓ Background tasks started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    stop_background_tasks()
    logger.info("✓ Background tasks stopped")


# ==================== FASTAPI APP INITIALIZATION ====================

app = FastAPI(
    title=settings.app_name,
    description="Advanced URL Shortener with Analytics and Caching",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ==================== MIDDLEWARE ====================

# CORS middleware - allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware - must be added after CORS
app.add_middleware(RateLimitMiddleware)


# ==================== ROUTES ====================

app.include_router(router)


# ==================== ROOT ENDPOINT ====================

@app.get("/", tags=["Info"])
def read_root():
    """Root endpoint with API information"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "create": "POST /shorten",
            "redirect": "GET /{short_code}",
            "stats": "GET /stats/{short_code}",
            "info": "GET /info/{short_code}",
            "delete": "DELETE /{short_code}",
            "health": "GET /health",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "features": [
            "Custom short codes",
            "URL expiry (1-365 days)",
            "Click tracking and analytics",
            "Redis caching for performance",
            "Rate limiting per IP",
            "Background analytics aggregation",
            "Device and referrer tracking"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
