"""
Background Tasks Scheduler
Runs periodic cleanup and maintenance tasks
"""
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config.environment import is_docker_desktop

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """
    Manages background tasks like:
    - Cleaning up expired preview deployments
    - Health monitoring
    - Cache cleanup
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.enabled = is_docker_desktop()  # Only run in Docker Desktop
    
    async def start(self):
        """Start background scheduler"""
        if not self.enabled:
            logger.info("⏭️ Background scheduler not started (K8s mode)")
            return
        
        logger.info("⏰ Starting background scheduler...")
        
        # Add jobs
        
        # Cleanup expired previews every hour
        self.scheduler.add_job(
            self._cleanup_expired_previews,
            'interval',
            hours=1,
            id='cleanup_previews',
            name='Cleanup Expired Previews'
        )
        
        # Health check previews every 5 minutes
        self.scheduler.add_job(
            self._health_check_previews,
            'interval',
            minutes=5,
            id='health_check',
            name='Preview Health Check'
        )
        
        self.scheduler.start()
        logger.info("✅ Background scheduler started (2 jobs)")
    
    async def stop(self):
        """Stop scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("✅ Background scheduler stopped")
    
    async def _cleanup_expired_previews(self):
        """Cleanup expired preview deployments"""
        try:
            from services.preview_deployment import get_preview_service
            
            preview_service = get_preview_service()
            count = await preview_service.cleanup_expired_previews()
            
            if count > 0:
                logger.info(f"🧹 Cleaned up {count} expired preview(s)")
                
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")
    
    async def _health_check_previews(self):
        """Check health of active previews"""
        try:
            from services.preview_deployment import get_preview_service
            from services.postgres_service import get_postgres_service
            import httpx
            
            preview_service = get_preview_service()
            db = get_postgres_service()
            
            # Get active previews
            previews = await preview_service.list_active_previews()
            
            for preview in previews:
                try:
                    fallback_url = preview.get("fallback_url")
                    
                    if fallback_url:
                        async with httpx.AsyncClient() as client:
                            response = await client.get(fallback_url, timeout=5)
                            
                            health = "healthy" if response.status_code == 200 else "unhealthy"
                            
                            # Update health status
                            await db.execute("""
                                UPDATE preview_deployments
                                SET health_status = $1, last_health_check = NOW()
                                WHERE task_id = $2
                            """, health, preview["task_id"])
                            
                except Exception as e:
                    # Mark as unhealthy
                    await db.execute("""
                        UPDATE preview_deployments
                        SET health_status = 'unreachable', last_health_check = NOW()
                        WHERE task_id = $1
                    """, preview["task_id"])
                    
        except Exception as e:
            logger.error(f"Error in health check job: {e}")


# Singleton instance
_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create BackgroundScheduler singleton"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler
