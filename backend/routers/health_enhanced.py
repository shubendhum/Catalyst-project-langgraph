"""
Enhanced Health Check Endpoint
Comprehensive health checks for all dependencies
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Literal
import time
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

StatusType = Literal["ok", "degraded", "down", "error"]


async def check_mongodb() -> Dict[str, Any]:
    """Check MongoDB connectivity"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.getenv("MONGO_URL")
        if not mongo_url:
            return {
                "status": "error",
                "detail": "MONGO_URL not configured"
            }
        
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=3000)
        await client.server_info()
        
        return {
            "status": "ok",
            "detail": "Connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Connection failed: {str(e)[:100]}"
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import redis.asyncio as aioredis
        
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        r = aioredis.from_url(redis_url, socket_timeout=3)
        
        await r.ping()
        await r.close()
        
        return {
            "status": "ok",
            "detail": "Connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Connection failed: {str(e)[:100]}"
        }


async def check_qdrant() -> Dict[str, Any]:
    """Check Qdrant connectivity"""
    try:
        import httpx
        
        url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/readyz", timeout=3.0)
            
            if response.status_code == 200:
                return {
                    "status": "ok",
                    "detail": "Connected"
                }
            else:
                return {
                    "status": "error",
                    "detail": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Connection failed: {str(e)[:100]}"
        }


async def check_llm() -> Dict[str, Any]:
    """Check LLM provider configuration"""
    try:
        # Check if API key is configured
        llm_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        provider = os.getenv("DEFAULT_LLM_PROVIDER", "emergent")
        model = os.getenv("DEFAULT_LLM_MODEL", "unknown")
        
        if not llm_key:
            return {
                "status": "error",
                "detail": "No LLM API key configured"
            }
        
        # Verify key format (basic check)
        if len(llm_key) > 10:
            return {
                "status": "ok",
                "detail": f"Provider: {provider}, Model: {model}, API key configured"
            }
        else:
            return {
                "status": "error",
                "detail": "Invalid API key format"
            }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Check failed: {str(e)[:100]}"
        }


async def check_rabbitmq() -> Dict[str, Any]:
    """Check RabbitMQ connectivity"""
    try:
        import pika
        
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://catalyst:catalyst_queue_2025@rabbitmq:5672/catalyst")
        
        # Parse connection parameters
        params = pika.URLParameters(rabbitmq_url)
        params.socket_timeout = 3
        
        connection = pika.BlockingConnection(params)
        connection.close()
        
        return {
            "status": "healthy",
            "detail": "Connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "detail": f"Connection failed: {str(e)[:100]}"
        }


@router.get("/health")
async def comprehensive_health_check():
    """
    Comprehensive health check endpoint
    
    Returns structured status for all dependencies
    """
    start_time = time.time()
    
    try:
        # Check all dependencies in parallel
        mongo_task = asyncio.create_task(check_mongodb())
        redis_task = asyncio.create_task(check_redis())
        qdrant_task = asyncio.create_task(check_qdrant())
        llm_task = asyncio.create_task(check_llm())
        rabbitmq_task = asyncio.create_task(check_rabbitmq())
        
        mongo_status = await mongo_task
        redis_status = await redis_task
        qdrant_status = await qdrant_task
        llm_status = await llm_task
        rabbitmq_status = await rabbitmq_task
        
        # Determine overall status
        statuses = [
            mongo_status["status"],
            redis_status["status"],
            qdrant_status["status"],
            llm_status["status"],
            rabbitmq_status["status"]
        ]
        
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "degraded"
        else:
            overall_status = "degraded"
        
        latency_ms = (time.time() - start_time) * 1000
        
        response = {
            "status": overall_status,
            "timestamp": time.time(),
            "checks": {
                "mongodb": mongo_status,
                "redis": redis_status,
                "qdrant": qdrant_status,
                "llm": llm_status,
                "rabbitmq": rabbitmq_status
            },
            "latency_ms": latency_ms
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e),
            "latency_ms": (time.time() - start_time) * 1000
        }


@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for docker healthcheck"""
    return {"status": "ok"}
