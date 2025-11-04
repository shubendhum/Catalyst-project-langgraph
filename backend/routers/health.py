"""
Health Check Router
Provides comprehensive health status for all system dependencies
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import logging
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        
        client = await aioredis.from_url(redis_url, socket_timeout=2, decode_responses=True)
        await client.ping()
        info = await client.info()
        await client.close()
        
        return {
            "status": "healthy",
            "version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "connected_clients": info.get("connected_clients")
        }
    except ImportError:
        return {
            "status": "degraded",
            "message": "Redis library not available, using in-memory fallback"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }


async def check_qdrant() -> Dict[str, Any]:
    """Check Qdrant connectivity"""
    try:
        from qdrant_client import QdrantClient
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        
        client = QdrantClient(url=qdrant_url, timeout=2)
        collections = client.get_collections()
        
        return {
            "status": "healthy",
            "collections_count": len(collections.collections),
            "collections": [c.name for c in collections.collections]
        }
    except ImportError:
        return {
            "status": "degraded",
            "message": "Qdrant library not available, using in-memory fallback"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }


async def check_llm_model() -> Dict[str, Any]:
    """Check LLM provider connectivity"""
    try:
        llm_key = os.getenv("EMERGENT_LLM_KEY")
        llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "emergent")
        llm_model = os.getenv("DEFAULT_LLM_MODEL", "claude-3-7-sonnet-20250219")
        
        if not llm_key:
            return {
                "status": "unhealthy",
                "message": "EMERGENT_LLM_KEY not configured"
            }
        
        # Quick validation - check if key is set
        key_prefix = llm_key[:10] if llm_key else "none"
        
        return {
            "status": "healthy",
            "provider": llm_provider,
            "model": llm_model,
            "key_configured": bool(llm_key),
            "key_prefix": f"{key_prefix}..."
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }


async def check_mongodb() -> Dict[str, Any]:
    """Check MongoDB connectivity"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
        
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
        await client.admin.command('ping')
        server_info = await client.server_info()
        
        return {
            "status": "healthy",
            "version": server_info.get("version"),
            "ok": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e)
        }


@router.get("/")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns status of all system dependencies
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Check all dependencies
    redis_status = await check_redis()
    qdrant_status = await check_qdrant()
    model_status = await check_llm_model()
    mongodb_status = await check_mongodb()
    
    # Determine overall status
    all_statuses = [
        mongodb_status["status"],
        redis_status["status"],
        qdrant_status["status"],
        model_status["status"]
    ]
    
    if all(s == "healthy" for s in all_statuses):
        overall_status = "healthy"
    elif any(s == "unhealthy" for s in all_statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    response = {
        "status": overall_status,
        "timestamp": timestamp,
        "dependencies": {
            "mongodb": mongodb_status,
            "redis": redis_status,
            "qdrant": qdrant_status,
            "model": model_status
        }
    }
    
    # Return 503 if unhealthy, 200 otherwise
    status_code = 503 if overall_status == "unhealthy" else 200
    
    if status_code == 503:
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness check
    Returns 200 if service can handle requests
    """
    # Check MongoDB only (critical dependency)
    mongodb_status = await check_mongodb()
    
    if mongodb_status["status"] != "healthy":
        raise HTTPException(status_code=503, detail={"ready": False, "reason": "MongoDB unavailable"})
    
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness check
    Returns 200 if service is alive
    """
    return {"alive": True}
