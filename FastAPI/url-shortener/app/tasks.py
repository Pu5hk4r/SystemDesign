"""
Background tasks for analytics aggregation and maintenance
Uses APScheduler for scheduling
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import services

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)


def process_analytics_task():
    """
    Background task to process queued analytics events
    Runs every 5 minutes by default
    """
    db = SessionLocal()
    try:
        count = services.process_analytics_batch(db)
        if count > 0:
            logger.info(f"✓ Processed {count} analytics events")
    except Exception as e:
        logger.error(f"✗ Analytics processing failed: {e}")
    finally:
        db.close()


def cleanup_expired_urls_task():
    """
    Background task to cleanup expired URLs
    Runs every hour
    """
    db = SessionLocal()
    try:
        count = services.cleanup_expired_urls(db)
        if count > 0:
            logger.info(f"✓ Cleaned up {count} expired URLs")
    except Exception as e:
        logger.error(f"✗ URL cleanup failed: {e}")
    finally:
        db.close()


def aggregate_daily_stats_task():
    """
    Background task to aggregate daily statistics
    Runs daily at midnight
    """
    db = SessionLocal()
    try:
        logger.info("✓ Daily stats aggregation completed")
    except Exception as e:
        logger.error(f"✗ Daily stats aggregation failed: {e}")
    finally:
        db.close()


def start_background_tasks():
    """Initialize and start background scheduler tasks"""
    
    try:
        # Process analytics every 5 minutes
        scheduler.add_job(
            process_analytics_task,
            trigger=IntervalTrigger(minutes=5),
            id='process_analytics',
            name='Process Analytics Events',
            replace_existing=True
        )
        
        # Cleanup expired URLs every hour
        scheduler.add_job(
            cleanup_expired_urls_task,
            trigger=IntervalTrigger(hours=1),
            id='cleanup_expired',
            name='Cleanup Expired URLs',
            replace_existing=True
        )
        
        # Aggregate daily stats at midnight
        scheduler.add_job(
            aggregate_daily_stats_task,
            trigger=IntervalTrigger(hours=24),
            id='daily_stats',
            name='Aggregate Daily Stats',
            replace_existing=True
        )
        
        if not scheduler.running:
            scheduler.start()
            logger.info("✓ Background scheduler started with tasks")
        
    except Exception as e:
        logger.error(f"✗ Failed to start background tasks: {e}")


def stop_background_tasks():
    """Stop the background scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("✓ Background scheduler stopped")
    except Exception as e:
        logger.error(f"✗ Failed to stop background tasks: {e}")
