"""
System Health Check and Observability
Provides detailed health status of all interdependent services
"""
import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SystemHealthCheck:
    """
    Centralized health checking for all system dependencies
    """
    
    def __init__(self):
        self.checks = {}
        self.startup_time = datetime.utcnow()
    
    async def check_mongodb(self, mongo_client) -> Dict[str, Any]:
        """Check MongoDB connection and status"""
        try:
            # Ping database
            await mongo_client.admin.command('ping')
            
            # Get server info
            server_info = await mongo_client.server_info()
            
            logger.info("✅ MongoDB: HEALTHY (version %s)", server_info.get('version', 'unknown'))
            
            return {
                "status": ServiceStatus.HEALTHY,
                "message": "Connected and responsive",
                "version": server_info.get('version'),
                "details": {
                    "max_bson_size": server_info.get('maxBsonObjectSize'),
                    "max_message_size": server_info.get('maxMessageSizeBytes')
                }
            }
        except Exception as e:
            logger.error("❌ MongoDB: UNHEALTHY - %s", str(e))
            return {
                "status": ServiceStatus.UNHEALTHY,
                "message": f"Connection failed: {str(e)}",
                "error": str(e)
            }
    
    async def check_postgres(self, postgres_url: str) -> Dict[str, Any]:
        """Check PostgreSQL connection and status"""
        try:
            import asyncpg
            
            conn = await asyncpg.connect(postgres_url)
            
            # Test query
            version = await conn.fetchval('SELECT version()')
            
            # Get database size
            db_name = postgres_url.split('/')[-1]
            size = await conn.fetchval(
                f"SELECT pg_size_pretty(pg_database_size('{db_name}'))"
            )
            
            await conn.close()
            
            logger.info("✅ PostgreSQL: HEALTHY (size: %s)", size)
            
            return {
                "status": ServiceStatus.HEALTHY,
                "message": "Connected and responsive",
                "version": version.split(',')[0] if version else "unknown",
                "details": {
                    "database_size": size
                }
            }
        except ImportError:
            logger.warning("⚠️ PostgreSQL: UNKNOWN - asyncpg not installed")
            return {
                "status": ServiceStatus.UNKNOWN,
                "message": "asyncpg library not available"
            }
        except Exception as e:
            logger.warning("⚠️ PostgreSQL: DEGRADED - %s", str(e))
            return {
                "status": ServiceStatus.DEGRADED,
                "message": f"Not available: {str(e)}",
                "error": str(e)
            }
    
    async def check_redis(self, redis_url: str) -> Dict[str, Any]:
        """Check Redis connection and status"""
        try:
            import redis.asyncio as aioredis
            
            # Parse URL and connect
            redis_client = await aioredis.from_url(redis_url, decode_responses=True)
            
            # Ping Redis
            pong = await redis_client.ping()
            
            # Get info
            info = await redis_client.info()
            
            await redis_client.close()
            
            logger.info("✅ Redis: HEALTHY (version %s)", info.get('redis_version', 'unknown'))
            
            return {
                "status": ServiceStatus.HEALTHY,
                "message": "Connected and responsive",
                "version": info.get('redis_version'),
                "details": {
                    "used_memory": info.get('used_memory_human'),
                    "connected_clients": info.get('connected_clients'),
                    "uptime_seconds": info.get('uptime_in_seconds')
                }
            }
        except ImportError:
            logger.warning("⚠️ Redis: DEGRADED - redis library not installed, using in-memory fallback")
            return {
                "status": ServiceStatus.DEGRADED,
                "message": "Not available, using in-memory cache fallback",
                "fallback": "in-memory"
            }
        except Exception as e:
            logger.warning("⚠️ Redis: DEGRADED - %s (using in-memory fallback)", str(e))
            return {
                "status": ServiceStatus.DEGRADED,
                "message": f"Not available: {str(e)}, using in-memory cache fallback",
                "fallback": "in-memory",
                "error": str(e)
            }
    
    async def check_qdrant(self, qdrant_url: str) -> Dict[str, Any]:
        """Check Qdrant connection and status"""
        try:
            from qdrant_client import QdrantClient
            
            client = QdrantClient(url=qdrant_url)
            
            # Get collections
            collections = client.get_collections()
            
            logger.info("✅ Qdrant: HEALTHY (%d collections)", len(collections.collections))
            
            return {
                "status": ServiceStatus.HEALTHY,
                "message": "Connected and responsive",
                "details": {
                    "collections_count": len(collections.collections),
                    "collections": [c.name for c in collections.collections]
                }
            }
        except ImportError:
            logger.warning("⚠️ Qdrant: DEGRADED - qdrant-client not installed, using in-memory fallback")
            return {
                "status": ServiceStatus.DEGRADED,
                "message": "Not available, using in-memory vector storage fallback",
                "fallback": "in-memory"
            }
        except Exception as e:
            logger.warning("⚠️ Qdrant: DEGRADED - %s (using in-memory fallback)", str(e))
            return {
                "status": ServiceStatus.DEGRADED,
                "message": f"Not available: {str(e)}, using in-memory vector storage fallback",
                "fallback": "in-memory",
                "error": str(e)
            }
    
    async def check_rabbitmq(self, rabbitmq_url: str) -> Dict[str, Any]:
        """Check RabbitMQ connection and status"""
        try:
            import pika
            
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            channel = connection.channel()
            
            # Get queue info
            queue_info = {}
            for queue_name in ['planner-queue', 'architect-queue', 'coder-queue']:
                try:
                    queue = channel.queue_declare(queue=queue_name, passive=True)
                    queue_info[queue_name] = {
                        "messages": queue.method.message_count,
                        "consumers": queue.method.consumer_count
                    }
                except:
                    pass
            
            connection.close()
            
            logger.info("✅ RabbitMQ: HEALTHY (%d queues monitored)", len(queue_info))
            
            return {
                "status": ServiceStatus.HEALTHY,
                "message": "Connected and responsive",
                "details": {
                    "queues": queue_info
                }
            }
        except ImportError:
            logger.warning("⚠️ RabbitMQ: UNKNOWN - pika not installed")
            return {
                "status": ServiceStatus.UNKNOWN,
                "message": "pika library not available"
            }
        except Exception as e:
            logger.warning("⚠️ RabbitMQ: DEGRADED - %s", str(e))
            return {
                "status": ServiceStatus.DEGRADED,
                "message": f"Not available: {str(e)}",
                "error": str(e)
            }
    
    async def check_all_services(
        self,
        mongo_client=None,
        postgres_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        rabbitmq_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check all services and return comprehensive health status
        """
        logger.info("🔍 Running system health checks...")
        
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
            "services": {}
        }
        
        # Check MongoDB (required)
        if mongo_client:
            health_status["services"]["mongodb"] = await self.check_mongodb(mongo_client)
        
        # Check PostgreSQL (optional)
        if postgres_url:
            health_status["services"]["postgres"] = await self.check_postgres(postgres_url)
        
        # Check Redis (optional, has fallback)
        if redis_url:
            health_status["services"]["redis"] = await self.check_redis(redis_url)
        
        # Check Qdrant (optional, has fallback)
        if qdrant_url:
            health_status["services"]["qdrant"] = await self.check_qdrant(qdrant_url)
        
        # Check RabbitMQ (optional for K8s, required for Docker Desktop)
        if rabbitmq_url:
            health_status["services"]["rabbitmq"] = await self.check_rabbitmq(rabbitmq_url)
        
        # Calculate overall status
        statuses = [s["status"] for s in health_status["services"].values()]
        if all(s == ServiceStatus.HEALTHY for s in statuses):
            health_status["overall_status"] = ServiceStatus.HEALTHY
            health_status["message"] = "All services healthy"
        elif any(s == ServiceStatus.UNHEALTHY for s in statuses):
            health_status["overall_status"] = ServiceStatus.UNHEALTHY
            health_status["message"] = "One or more critical services unhealthy"
        elif any(s == ServiceStatus.DEGRADED for s in statuses):
            health_status["overall_status"] = ServiceStatus.DEGRADED
            health_status["message"] = "Running in degraded mode with fallbacks"
        else:
            health_status["overall_status"] = ServiceStatus.UNKNOWN
            health_status["message"] = "Unable to determine health status"
        
        self._log_health_summary(health_status)
        
        return health_status
    
    def _log_health_summary(self, health_status: Dict[str, Any]):
        """Log a clear summary of system health"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 SYSTEM HEALTH STATUS")
        logger.info("=" * 80)
        logger.info("Overall Status: %s", health_status["overall_status"].upper())
        logger.info("")
        
        for service_name, service_status in health_status["services"].items():
            status = service_status["status"]
            message = service_status["message"]
            
            if status == ServiceStatus.HEALTHY:
                emoji = "✅"
            elif status == ServiceStatus.DEGRADED:
                emoji = "⚠️"
            elif status == ServiceStatus.UNHEALTHY:
                emoji = "❌"
            else:
                emoji = "❓"
            
            logger.info("%s %s: %s - %s", emoji, service_name.upper(), status.upper(), message)
            
            # Log details if available
            if "version" in service_status:
                logger.info("   └─ Version: %s", service_status["version"])
            if "fallback" in service_status:
                logger.info("   └─ Fallback: %s", service_status["fallback"])
        
        logger.info("=" * 80)
        logger.info("")


# Global instance
_health_checker = None


def get_health_checker() -> SystemHealthCheck:
    """Get or create SystemHealthCheck singleton"""
    global _health_checker
    if _health_checker is None:
        _health_checker = SystemHealthCheck()
    return _health_checker
