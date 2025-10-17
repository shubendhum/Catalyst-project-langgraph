"""
Caching Service
Caches LLM responses, code patterns, and frequently accessed data
"""
import logging
import hashlib
import json
from typing import Dict, Optional, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class CachingService:
    """
    Multi-level caching service for performance optimization
    """
    
    def __init__(self, db):
        self.db = db
        
        # In-memory cache for hot data
        self.memory_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Cache TTLs (in seconds)
        self.ttls = {
            "llm_response": 3600,  # 1 hour
            "code_pattern": 86400,  # 24 hours
            "agent_result": 7200,  # 2 hours
            "mcp_tool_result": 1800  # 30 minutes
        }
    
    def _generate_cache_key(self, cache_type: str, **kwargs) -> str:
        """Generate unique cache key from parameters"""
        # Sort keys for consistent hashing
        sorted_kwargs = sorted(kwargs.items())
        key_string = f"{cache_type}:{json.dumps(sorted_kwargs, sort_keys=True)}"
        
        # Hash for shorter key
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, cache_type: str, **kwargs) -> Optional[Any]:
        """Get cached value"""
        try:
            cache_key = self._generate_cache_key(cache_type, **kwargs)
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                cached_data = self.memory_cache[cache_key]
                
                # Check if expired
                if datetime.now(timezone.utc) < cached_data["expires_at"]:
                    self.cache_hits += 1
                    logger.debug(f"Cache hit (memory): {cache_key}")
                    return cached_data["value"]
                else:
                    # Expired, remove from memory
                    del self.memory_cache[cache_key]
            
            # Check database cache
            cached_doc = await self.db.cache.find_one({"key": cache_key})
            
            if cached_doc:
                expires_at = datetime.fromisoformat(cached_doc["expires_at"])
                
                if datetime.now(timezone.utc) < expires_at:
                    self.cache_hits += 1
                    logger.debug(f"Cache hit (database): {cache_key}")
                    
                    # Promote to memory cache
                    self.memory_cache[cache_key] = {
                        "value": cached_doc["value"],
                        "expires_at": expires_at
                    }
                    
                    return cached_doc["value"]
                else:
                    # Expired, remove from database
                    await self.db.cache.delete_one({"key": cache_key})
            
            # Cache miss
            self.cache_misses += 1
            logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    async def set(
        self,
        cache_type: str,
        value: Any,
        ttl: Optional[int] = None,
        **kwargs
    ):
        """Set cached value"""
        try:
            cache_key = self._generate_cache_key(cache_type, **kwargs)
            
            # Use default TTL if not provided
            if ttl is None:
                ttl = self.ttls.get(cache_type, 3600)
            
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            
            cached_data = {
                "value": value,
                "expires_at": expires_at
            }
            
            # Store in memory cache
            self.memory_cache[cache_key] = cached_data
            
            # Store in database cache
            cache_doc = {
                "key": cache_key,
                "type": cache_type,
                "value": value,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.cache.update_one(
                {"key": cache_key},
                {"$set": cache_doc},
                upsert=True
            )
            
            logger.debug(f"Cached: {cache_key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
    
    async def invalidate(self, cache_type: str, **kwargs):
        """Invalidate specific cache entry"""
        try:
            cache_key = self._generate_cache_key(cache_type, **kwargs)
            
            # Remove from memory
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            # Remove from database
            await self.db.cache.delete_one({"key": cache_key})
            
            logger.debug(f"Invalidated cache: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
    
    async def invalidate_by_type(self, cache_type: str):
        """Invalidate all cache entries of a specific type"""
        try:
            # Remove from memory
            keys_to_remove = [
                key for key, data in self.memory_cache.items()
                if key.startswith(f"{cache_type}:")
            ]
            for key in keys_to_remove:
                del self.memory_cache[key]
            
            # Remove from database
            result = await self.db.cache.delete_many({"type": cache_type})
            
            logger.info(f"Invalidated {result.deleted_count} cache entries of type: {cache_type}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache by type: {str(e)}")
    
    async def clear_all(self):
        """Clear all cache"""
        try:
            self.memory_cache.clear()
            result = await self.db.cache.delete_many({})
            logger.info(f"Cleared all cache ({result.deleted_count} entries)")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    async def cleanup_expired(self):
        """Remove expired entries from cache"""
        try:
            now = datetime.now(timezone.utc)
            
            # Clean memory cache
            expired_keys = [
                key for key, data in self.memory_cache.items()
                if now >= data["expires_at"]
            ]
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Clean database cache
            result = await self.db.cache.delete_many({
                "expires_at": {"$lt": now.isoformat()}
            })
            
            if expired_keys or result.deleted_count > 0:
                logger.info(f"Cleaned up {len(expired_keys)} memory + {result.deleted_count} database expired entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "memory_cache_size": len(self.memory_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    async def cache_llm_response(self, prompt: str, model: str, response: str):
        """Cache LLM response"""
        await self.set(
            "llm_response",
            response,
            prompt=prompt,
            model=model
        )
    
    async def get_cached_llm_response(self, prompt: str, model: str) -> Optional[str]:
        """Get cached LLM response"""
        return await self.get(
            "llm_response",
            prompt=prompt,
            model=model
        )
    
    async def cache_code_pattern(self, pattern_type: str, context: str, code: str):
        """Cache code generation pattern"""
        await self.set(
            "code_pattern",
            code,
            pattern_type=pattern_type,
            context=context
        )
    
    async def get_cached_code_pattern(self, pattern_type: str, context: str) -> Optional[str]:
        """Get cached code pattern"""
        return await self.get(
            "code_pattern",
            pattern_type=pattern_type,
            context=context
        )


# Global caching service instance
_caching_service = None


def get_caching_service(db) -> CachingService:
    """Get or create caching service singleton"""
    global _caching_service
    if _caching_service is None:
        _caching_service = CachingService(db)
    return _caching_service
