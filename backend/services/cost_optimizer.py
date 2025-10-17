"""
Cost Optimizer Service
Reduces LLM costs through intelligent caching, model selection, and token optimization
Uses Redis when available, falls back to in-memory cache
"""

import hashlib
import json
import os
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone, timedelta
from cachetools import TTLCache
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class CostOptimizer:
    """Optimizes LLM costs through caching and smart model selection"""
    
    # Model costs per 1K tokens (input/output average)
    MODEL_COSTS = {
        "claude-3-7-sonnet-20250219": 0.003,
        "claude-3-5-sonnet-20240620": 0.003,
        "claude-3-opus-20240229": 0.015,
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.0015,
        "gemini-pro": 0.00025,
    }
    
    # Model capabilities (complexity score 0-1)
    MODEL_CAPABILITIES = {
        "claude-3-opus-20240229": 1.0,
        "claude-3-7-sonnet-20250219": 0.9,
        "gpt-4o": 0.85,
        "claude-3-5-sonnet-20240620": 0.85,
        "gpt-4": 0.8,
        "gpt-4o-mini": 0.6,
        "gpt-3.5-turbo": 0.5,
        "gemini-pro": 0.6,
    }
    
    def __init__(self, db=None):
        self.db = db
        
        # Try to connect to Redis first
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"✅ Connected to Redis at {redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
                self.redis_client = None
        
        # In-memory cache as fallback
        self.response_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL
        
        # Semantic cache for embeddings (if we had vector DB)
        self.semantic_cache_enabled = False
        
        # Budget tracking
        self.budgets = {}  # project_id -> budget info
    
    def generate_cache_key(
        self, 
        prompt: str, 
        model: str, 
        temperature: float = 0.7
    ) -> str:
        """Generate cache key for prompt"""
        # Create deterministic hash
        cache_data = {
            "prompt": prompt.strip(),
            "model": model,
            "temperature": round(temperature, 2)
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def get_cached_response(
        self, 
        prompt: str, 
        model: str,
        temperature: float = 0.7
    ) -> Optional[Dict]:
        """Check cache for existing response"""
        cache_key = self.generate_cache_key(prompt, model, temperature)
        
        # Try Redis first
        if self.redis_client:
            try:
                cached_str = self.redis_client.get(f"llm_cache:{cache_key}")
                if cached_str:
                    cached = json.loads(cached_str)
                    logger.info(f"✅ Redis cache hit (saved ${cached.get('cost_saved', 0):.4f})")
                    return {
                        "response": cached["response"],
                        "cached": True,
                        "cache_timestamp": cached["timestamp"],
                        "cost_saved": cached.get("cost_saved", 0),
                        "cache_type": "redis"
                    }
            except Exception as e:
                logger.error(f"Redis cache read error: {e}")
        
        # Fall back to in-memory cache
        cached = self.response_cache.get(cache_key)
        if cached:
            logger.info(f"✅ Memory cache hit (saved ${cached.get('cost_saved', 0):.4f})")
            return {
                "response": cached["response"],
                "cached": True,
                "cache_timestamp": cached["timestamp"],
                "cost_saved": cached.get("cost_saved", 0),
                "cache_type": "memory"
            }
        
        return None
    
    def cache_response(
        self,
        prompt: str,
        model: str,
        response: str,
        tokens_used: int,
        temperature: float = 0.7
    ):
        """Cache response for future use"""
        cache_key = self.generate_cache_key(prompt, model, temperature)
        
        cost = self.calculate_cost(tokens_used, model)
        
        self.response_cache[cache_key] = {
            "response": response,
            "tokens": tokens_used,
            "cost_saved": cost,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model
        }
        
        logger.info(f"Cached response for future use (potential saving: ${cost:.4f})")
    
    def calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost for token usage"""
        cost_per_1k = self.MODEL_COSTS.get(model, 0.003)
        return (tokens / 1000) * cost_per_1k
    
    def select_optimal_model(
        self,
        task_description: str,
        complexity: float,
        budget_remaining: Optional[float] = None,
        current_model: str = "claude-3-7-sonnet-20250219"
    ) -> Dict:
        """
        Select most cost-effective model for task
        
        Args:
            task_description: What the task involves
            complexity: Estimated complexity (0-1)
            budget_remaining: Budget left for project
            current_model: Current model being used
        """
        # Get task complexity if not provided
        if complexity is None:
            complexity = self._estimate_complexity(task_description)
        
        # Find models that can handle this complexity
        suitable_models = []
        for model, capability in self.MODEL_CAPABILITIES.items():
            if capability >= complexity:
                suitable_models.append({
                    "model": model,
                    "capability": capability,
                    "cost": self.MODEL_COSTS.get(model, 0.003),
                    "overkill": capability - complexity  # How much extra capability
                })
        
        # Sort by cost (cheapest first)
        suitable_models.sort(key=lambda x: x["cost"])
        
        if not suitable_models:
            # Fallback to most capable model
            return {
                "recommended_model": "claude-3-opus-20240229",
                "reason": "Task complexity requires most capable model",
                "cost_per_1k": self.MODEL_COSTS["claude-3-opus-20240229"],
                "estimated_savings": 0
            }
        
        # Select cheapest suitable model
        selected = suitable_models[0]
        current_cost = self.MODEL_COSTS.get(current_model, 0.003)
        
        return {
            "recommended_model": selected["model"],
            "current_model": current_model,
            "reason": f"Handles complexity {complexity:.2f} at lowest cost",
            "cost_per_1k": selected["cost"],
            "current_cost_per_1k": current_cost,
            "estimated_savings_percent": ((current_cost - selected["cost"]) / current_cost * 100) if current_cost > 0 else 0,
            "complexity_match": selected["capability"],
            "alternatives": [m["model"] for m in suitable_models[1:3]]  # Show alternatives
        }
    
    def _estimate_complexity(self, task_description: str) -> float:
        """Estimate task complexity from description"""
        description_lower = task_description.lower()
        
        # Keywords indicating high complexity
        high_complexity_keywords = [
            "architecture", "design", "complex", "enterprise",
            "distributed", "microservices", "security", "scale",
            "optimization", "refactor", "debug difficult"
        ]
        
        # Keywords indicating low complexity
        low_complexity_keywords = [
            "simple", "basic", "quick", "small change",
            "formatting", "typo", "comment", "documentation",
            "rename", "copy", "duplicate"
        ]
        
        # Keywords indicating medium complexity
        medium_complexity_keywords = [
            "feature", "implement", "create", "build",
            "api", "endpoint", "function", "component"
        ]
        
        # Count matches
        high_score = sum(1 for kw in high_complexity_keywords if kw in description_lower)
        low_score = sum(1 for kw in low_complexity_keywords if kw in description_lower)
        medium_score = sum(1 for kw in medium_complexity_keywords if kw in description_lower)
        
        # Calculate complexity
        if high_score > low_score:
            return 0.8 + (min(high_score, 3) * 0.05)  # 0.8-0.95
        elif low_score > high_score and low_score > medium_score:
            return 0.3 + (min(low_score, 3) * 0.05)  # 0.3-0.45
        else:
            return 0.5 + (min(medium_score, 3) * 0.05)  # 0.5-0.65
    
    async def track_usage(
        self,
        project_id: str,
        task_id: str,
        model: str,
        tokens: int,
        cost: float
    ):
        """Track token usage and costs"""
        if not self.db:
            return
        
        usage_record = {
            "project_id": project_id,
            "task_id": task_id,
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await self.db.token_usage.insert_one(usage_record)
            
            # Update project totals
            await self.db.projects.update_one(
                {"id": project_id},
                {
                    "$inc": {
                        "total_tokens": tokens,
                        "total_cost": cost
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
    
    async def get_project_budget_status(self, project_id: str) -> Dict:
        """Get budget status for project"""
        if not self.db:
            return {
                "budget_set": False,
                "message": "Database not configured"
            }
        
        try:
            project = await self.db.projects.find_one({"id": project_id})
            if not project:
                return {"budget_set": False}
            
            budget = project.get("budget", {})
            if not budget.get("limit"):
                return {"budget_set": False}
            
            current_cost = project.get("total_cost", 0)
            budget_limit = budget["limit"]
            usage_percent = (current_cost / budget_limit * 100) if budget_limit > 0 else 0
            
            status = {
                "budget_set": True,
                "limit": budget_limit,
                "spent": current_cost,
                "remaining": budget_limit - current_cost,
                "usage_percent": usage_percent,
                "status": "ok"
            }
            
            if usage_percent >= 100:
                status["status"] = "exceeded"
                status["message"] = "Budget exceeded!"
            elif usage_percent >= 90:
                status["status"] = "critical"
                status["message"] = f"Budget almost exhausted ({usage_percent:.1f}%)"
            elif usage_percent >= 75:
                status["status"] = "warning"
                status["message"] = f"Budget usage high ({usage_percent:.1f}%)"
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting budget status: {e}")
            return {"budget_set": False, "error": str(e)}
    
    async def set_project_budget(
        self,
        project_id: str,
        budget_limit: float,
        alert_threshold: float = 0.75
    ):
        """Set budget for project"""
        if not self.db:
            return {"success": False, "message": "Database not configured"}
        
        try:
            await self.db.projects.update_one(
                {"id": project_id},
                {
                    "$set": {
                        "budget": {
                            "limit": budget_limit,
                            "alert_threshold": alert_threshold,
                            "set_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                }
            )
            
            return {
                "success": True,
                "message": f"Budget set to ${budget_limit}",
                "limit": budget_limit
            }
        except Exception as e:
            logger.error(f"Error setting budget: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_cost_analytics(
        self,
        project_id: Optional[str] = None,
        timeframe_days: int = 30
    ) -> Dict:
        """Get cost analytics"""
        if not self.db:
            return {"error": "Database not configured"}
        
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
            
            query = {"timestamp": {"$gte": start_date.isoformat()}}
            if project_id:
                query["project_id"] = project_id
            
            usage_records = await self.db.token_usage.find(query).to_list(length=None)
            
            if not usage_records:
                return {
                    "total_cost": 0,
                    "total_tokens": 0,
                    "requests": 0
                }
            
            total_cost = sum(r.get("cost", 0) for r in usage_records)
            total_tokens = sum(r.get("tokens", 0) for r in usage_records)
            
            # Group by model
            model_breakdown = {}
            for record in usage_records:
                model = record.get("model", "unknown")
                if model not in model_breakdown:
                    model_breakdown[model] = {"cost": 0, "tokens": 0, "requests": 0}
                
                model_breakdown[model]["cost"] += record.get("cost", 0)
                model_breakdown[model]["tokens"] += record.get("tokens", 0)
                model_breakdown[model]["requests"] += 1
            
            # Calculate daily average
            daily_average = total_cost / timeframe_days if timeframe_days > 0 else 0
            
            return {
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "requests": len(usage_records),
                "daily_average": daily_average,
                "model_breakdown": model_breakdown,
                "timeframe_days": timeframe_days,
                "cache_hits": len(self.response_cache),
                "estimated_savings": sum(
                    item.get("cost_saved", 0) 
                    for item in self.response_cache.values()
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting cost analytics: {e}")
            return {"error": str(e)}
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "cache_size": len(self.response_cache),
            "cache_maxsize": self.response_cache.maxsize,
            "cache_ttl_seconds": self.response_cache.ttl,
            "estimated_savings": sum(
                item.get("cost_saved", 0) 
                for item in self.response_cache.values()
            )
        }


def get_cost_optimizer(db=None) -> CostOptimizer:
    """Factory function to get cost optimizer"""
    return CostOptimizer(db)
