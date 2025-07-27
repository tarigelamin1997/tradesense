
"""
Background task system for periodic analytics and data processing
"""
from celery import Celery
from celery.schedules import crontab
import asyncio
from services.analytics_service import AnalyticsService
from db.connection import db_manager
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "tradesense",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'update-analytics-cache': {
        'task': 'backend.core.tasks.update_analytics_cache',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'calculate-behavioral-scores': {
        'task': 'backend.core.tasks.calculate_behavioral_scores',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'cleanup-old-data': {
        'task': 'backend.core.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}

@celery_app.task
def update_analytics_cache():
    """Update analytics cache for active users"""
    async def _update_cache():
        analytics_service = AnalyticsService()
        
        # Get active users (users who traded in last 7 days)
        async with db_manager.get_connection() as conn:
            users = await conn.fetch("""
                SELECT DISTINCT user_id 
                FROM trades 
                WHERE entry_time >= NOW() - INTERVAL '7 days'
            """)
            
            for user in users:
                try:
                    await analytics_service.get_user_analytics(user['user_id'])
                    logger.info(f"Updated cache for user {user['user_id']}")
                except Exception as e:
                    logger.error(f"Failed to update cache for user {user['user_id']}: {e}")
    
    asyncio.run(_update_cache())

@celery_app.task
def calculate_behavioral_scores():
    """Calculate and update behavioral analysis scores"""
    async def _calculate_scores():
        async with db_manager.get_connection() as conn:
            # Update behavioral flags for recent trades
            await conn.execute("""
                UPDATE trade_analytics 
                SET revenge_trade_flag = (
                    -- Logic to detect revenge trades
                    SELECT COUNT(*) > 0
                    FROM trades t1, trades t2
                    WHERE t1.user_id = t2.user_id
                    AND t1.exit_time < t2.entry_time
                    AND t1.pnl < 0
                    AND EXTRACT(EPOCH FROM (t2.entry_time - t1.exit_time))/60 < 30
                    AND t2.id = trade_analytics.trade_id
                )
                WHERE trade_id IN (
                    SELECT id FROM trades WHERE entry_time >= NOW() - INTERVAL '1 day'
                )
            """)
    
    asyncio.run(_calculate_scores())

@celery_app.task
def cleanup_old_data():
    """Clean up old cache entries and temporary data"""
    async def _cleanup():
        analytics_service = AnalyticsService()
        
        # Clear old Redis cache entries
        keys = analytics_service.redis_client.keys("analytics:*")
        if keys:
            analytics_service.redis_client.delete(*keys)
            logger.info(f"Cleaned up {len(keys)} old cache entries")
    
    asyncio.run(_cleanup())
