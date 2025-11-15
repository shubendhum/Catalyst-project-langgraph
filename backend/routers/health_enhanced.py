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


@router.get("/health")
async def comprehensive_health_check():
    """
    Comprehensive health check endpoint
    
    Returns structured status for all dependencies.
    Always returns HTTP 200 for backward compatibility.
    Check the 'status' field in the response body to determine actual health.
    
    Response format:
    {
      "status": "ok" | "degraded" | "down",
      "redis": {"status": "ok|error", "detail": "..."},
      "qdrant": {"status": "ok|error", "detail": "..."},
      "model": {"status": "ok|error", "detail": "..."},
      "timestamp": 1234567890.123,
      "latency_ms": 45.2
    }
    """
    start_time = time.time()
    
    try:
        # Check required dependencies in parallel
        redis_task = asyncio.create_task(check_redis())
        qdrant_task = asyncio.create_task(check_qdrant())
        llm_task = asyncio.create_task(check_llm())
        
        redis_status = await redis_task
        qdrant_status = await qdrant_task
        llm_status = await llm_task
        
        # Determine overall status
        # "ok" if all are ok
        # "degraded" if at least one is error but API can respond
        # "down" only if service cannot function (but since we're responding, we use degraded)
        statuses = [
            redis_status["status"],
            qdrant_status["status"],
            llm_status["status"]
        ]
        
        if all(s == "ok" for s in statuses):
            overall_status = "ok"
        elif any(s == "error" for s in statuses):
            overall_status = "degraded"
        else:
            overall_status = "ok"
        
        latency_ms = (time.time() - start_time) * 1000
        
        response = {
            "status": overall_status,
            "redis": redis_status,
            "qdrant": qdrant_status,
            "model": llm_status,
            "timestamp": time.time(),
            "latency_ms": latency_ms
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        # Still return 200 for backward compatibility, but status is down
        return {
            "status": "down",
            "redis": {"status": "error", "detail": "Check failed"},
            "qdrant": {"status": "error", "detail": "Check failed"},
            "model": {"status": "error", "detail": "Check failed"},
            "error": str(e)[:200],
            "timestamp": time.time(),
            "latency_ms": (time.time() - start_time) * 1000
        }


@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for docker healthcheck"""
    return {"status": "ok"}
