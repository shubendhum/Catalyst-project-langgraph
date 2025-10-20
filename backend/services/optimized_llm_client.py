"""
Optimized LLM Client with Cost Optimization
Wraps UnifiedLLMClient with caching, model selection, and budget tracking
Now includes LLM observability via Langfuse/Langsmith
"""

from typing import List, Optional, Dict, Any
from services.cost_optimizer import get_cost_optimizer
from services.context_manager import get_context_manager
from llm_client import UnifiedLLMClient
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import logging
import os
import time

logger = logging.getLogger(__name__)


class OptimizedLLMClient:
    """
    LLM client wrapper with automatic cost optimization:
    - Smart caching for similar requests
    - Intelligent model selection based on complexity
    - Budget tracking and enforcement
    - Context window management
    - Token usage monitoring
    """
    
    def __init__(
        self,
        db=None,
        project_id: Optional[str] = None,
        default_provider: str = "emergent",
        default_model: str = "claude-3-7-sonnet-20250219"
    ):
        """
        Initialize optimized LLM client
        
        Args:
            db: Database connection for tracking
            project_id: Project ID for budget tracking
            default_provider: Default LLM provider
            default_model: Default model to use
        """
        self.db = db
        self.project_id = project_id
        self.default_provider = default_provider
        self.default_model = default_model
        
        # Initialize cost optimizer and context manager
        self.cost_optimizer = get_cost_optimizer(db)
        self.context_manager = get_context_manager(default_model)
        
        # Current LLM client (will be initialized per call)
        self.base_client = None
        
        # Tracking
        self.calls_made = 0
        self.cache_hits = 0
        self.total_cost = 0.0
    
    async def ainvoke(
        self,
        messages: List[BaseMessage],
        task_description: str = "",
        complexity: Optional[float] = None,
        use_cache: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        force_model: Optional[str] = None
    ) -> AIMessage:
        """
        Invoke LLM with cost optimization
        
        Args:
            messages: List of messages (LangChain format)
            task_description: Description of task for complexity estimation
            complexity: Task complexity (0-1), auto-estimated if None
            use_cache: Whether to use caching
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
            force_model: Force specific model (skip optimization)
        
        Returns:
            AIMessage with LLM response
        """
        
        self.calls_made += 1
        
        # 1. Check cache first (if enabled)
        if use_cache:
            cached_response = await self._check_cache(
                messages, temperature, force_model or self.default_model
            )
            if cached_response:
                self.cache_hits += 1
                cache_hit_rate = (self.cache_hits / self.calls_made) * 100
                logger.info(f"💰 Cache hit! Rate: {cache_hit_rate:.1f}%")
                return AIMessage(content=cached_response["response"])
        
        # 2. Estimate complexity if not provided
        if complexity is None and task_description:
            complexity = self._estimate_complexity(task_description)
            logger.info(f"📊 Estimated complexity: {complexity:.2f}")
        elif complexity is None:
            complexity = 0.6  # Default medium complexity
        
        # 3. Select optimal model (unless forced)
        if force_model:
            selected_model = force_model
            logger.info(f"🔒 Using forced model: {selected_model}")
        else:
            model_recommendation = self.cost_optimizer.select_optimal_model(
                task_description or self._extract_task_from_messages(messages),
                complexity,
                current_model=self.default_model
            )
            selected_model = model_recommendation["recommended_model"]
            
            if selected_model != self.default_model:
                savings = model_recommendation.get("estimated_savings_percent", 0)
                logger.info(
                    f"💡 Optimized model: {selected_model} "
                    f"(saves {savings:.1f}% vs {self.default_model})"
                )
        
        # 4. Check project budget
        if self.project_id:
            budget_ok = await self._check_budget()
            if not budget_ok:
                raise Exception(
                    f"⛔ Project budget exceeded! "
                    f"Use /api/optimizer/budget/{self.project_id} to check status"
                )
        
        # 5. Manage context window
        messages = await self._manage_context(messages, selected_model)
        
        # 6. Initialize LLM client with selected model
        provider = self._get_provider_for_model(selected_model)
        self.base_client = UnifiedLLMClient(
            provider=provider,
            model=selected_model,
            api_key=os.getenv("EMERGENT_LLM_KEY")
        )
        
        # 7. Make LLM call
        try:
            logger.info(f"🤖 Calling {selected_model}...")
            response = await self.base_client.ainvoke(messages)
            
            # 8. Track usage and cost
            await self._track_usage(messages, response, selected_model)
            
            # 9. Cache response
            if use_cache:
                await self._cache_response(
                    messages, response, selected_model, temperature
                )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            raise
    
    async def _check_cache(
        self,
        messages: List[BaseMessage],
        temperature: float,
        model: str
    ) -> Optional[Dict]:
        """Check if response is cached"""
        prompt = self._messages_to_cache_key(messages)
        return self.cost_optimizer.get_cached_response(prompt, model, temperature)
    
    async def _cache_response(
        self,
        messages: List[BaseMessage],
        response: AIMessage,
        model: str,
        temperature: float
    ):
        """Cache LLM response"""
        prompt = self._messages_to_cache_key(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        tokens = self._estimate_token_count(messages, response)
        
        self.cost_optimizer.cache_response(
            prompt, model, response_text, tokens, temperature
        )
    
    def _messages_to_cache_key(self, messages: List[BaseMessage]) -> str:
        """Convert messages to cache key"""
        parts = []
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            parts.append(content)
        return " ".join(parts)
    
    def _estimate_complexity(self, task_description: str) -> float:
        """
        Estimate task complexity from description
        Returns: 0-1 complexity score
        """
        description_lower = task_description.lower()
        
        # High complexity indicators
        high_complexity_keywords = [
            "architecture", "design system", "complex", "distributed",
            "microservices", "optimization", "security audit",
            "performance tuning", "refactor large", "migrate"
        ]
        
        # Low complexity indicators
        low_complexity_keywords = [
            "simple", "basic", "quick", "small", "fix bug",
            "typo", "comment", "format", "rename", "copy",
            "boilerplate", "template"
        ]
        
        # Medium complexity indicators
        medium_complexity_keywords = [
            "create", "implement", "build", "add feature",
            "api", "endpoint", "component", "function"
        ]
        
        # Count matches
        high_count = sum(1 for kw in high_complexity_keywords if kw in description_lower)
        low_count = sum(1 for kw in low_complexity_keywords if kw in description_lower)
        medium_count = sum(1 for kw in medium_complexity_keywords if kw in description_lower)
        
        # Calculate complexity
        if high_count > 0:
            return min(0.8 + (high_count * 0.05), 1.0)
        elif low_count > 0:
            return max(0.2 + (low_count * 0.05), 0.3)
        elif medium_count > 0:
            return 0.5 + (medium_count * 0.05)
        else:
            return 0.6  # Default medium
    
    async def _check_budget(self) -> bool:
        """Check if project budget allows more calls"""
        budget_status = await self.cost_optimizer.get_project_budget_status(
            self.project_id
        )
        
        if not budget_status.get("budget_set"):
            return True  # No budget set, allow
        
        status = budget_status.get("status", "ok")
        
        if status == "exceeded":
            logger.error(f"⛔ Budget exceeded for project {self.project_id}")
            return False
        elif status == "critical":
            logger.warning(f"⚠️  Budget almost exhausted: {budget_status.get('message')}")
        
        return True
    
    async def _manage_context(
        self,
        messages: List[BaseMessage],
        model: str
    ) -> List[BaseMessage]:
        """Manage context window to prevent overflow"""
        
        # Update context manager with current model
        self.context_manager = get_context_manager(model)
        
        # Count tokens
        tokens = self.context_manager.count_messages_tokens(
            [{"role": self._get_role(m), "content": self._get_content(m)} for m in messages]
        )
        
        # Check limit
        status = self.context_manager.check_limit(tokens)
        
        if status["status"] == "critical":
            # Need to truncate
            logger.warning(f"⚠️  Context critical: {tokens} tokens, truncating...")
            
            message_dicts = [
                {"role": self._get_role(m), "content": self._get_content(m)}
                for m in messages
            ]
            
            truncated_dicts, metadata = self.context_manager.truncate_messages(
                message_dicts,
                strategy="important_first"
            )
            
            logger.info(
                f"✂️  Truncated {metadata['messages_removed']} messages, "
                f"{metadata['tokens_before']} → {metadata['tokens_after']} tokens"
            )
            
            # Convert back to BaseMessage objects
            messages = self._dicts_to_messages(truncated_dicts)
        
        elif status["status"] == "warning":
            logger.warning(f"⚠️  {status['message']}")
        
        return messages
    
    def _get_role(self, message: BaseMessage) -> str:
        """Get role from message"""
        if isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, AIMessage):
            return "assistant"
        elif isinstance(message, SystemMessage):
            return "system"
        else:
            return "user"
    
    def _get_content(self, message: BaseMessage) -> str:
        """Get content from message"""
        return message.content if hasattr(message, 'content') else str(message)
    
    def _dicts_to_messages(self, dicts: List[Dict]) -> List[BaseMessage]:
        """Convert dicts back to BaseMessage objects"""
        messages = []
        for d in dicts:
            role = d.get("role", "user")
            content = d.get("content", "")
            
            if role == "system":
                messages.append(SystemMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        
        return messages
    
    async def _track_usage(
        self,
        messages: List[BaseMessage],
        response: AIMessage,
        model: str
    ):
        """Track token usage and cost"""
        
        # Estimate tokens
        tokens_used = self._estimate_token_count(messages, response)
        
        # Calculate cost
        cost = self.cost_optimizer.calculate_cost(tokens_used, model)
        self.total_cost += cost
        
        # Log
        logger.info(
            f"📊 Tokens: {tokens_used}, Cost: ${cost:.4f}, "
            f"Total: ${self.total_cost:.4f}"
        )
        
        # Track in database if project ID available
        if self.project_id and self.db:
            try:
                await self.cost_optimizer.track_usage(
                    self.project_id,
                    f"task_{self.calls_made}",
                    model,
                    tokens_used,
                    cost
                )
            except Exception as e:
                logger.error(f"Failed to track usage: {e}")
    
    def _estimate_token_count(
        self,
        messages: List[BaseMessage],
        response: AIMessage
    ) -> int:
        """Estimate total token count"""
        
        # Convert messages to dicts
        message_dicts = [
            {"role": self._get_role(m), "content": self._get_content(m)}
            for m in messages
        ]
        
        prompt_tokens = self.context_manager.count_messages_tokens(message_dicts)
        response_text = response.content if hasattr(response, 'content') else str(response)
        response_tokens = self.context_manager.count_tokens(response_text)
        
        return prompt_tokens + response_tokens
    
    def _get_provider_for_model(self, model: str) -> str:
        """Determine provider from model name"""
        model_lower = model.lower()
        
        if "gpt" in model_lower:
            return "emergent"  # Using Emergent LLM Key for OpenAI
        elif "claude" in model_lower:
            return "emergent"  # Using Emergent LLM Key for Anthropic
        elif "gemini" in model_lower:
            return "emergent"  # Using Emergent LLM Key for Google
        else:
            return "emergent"  # Default to Emergent
    
    def _extract_task_from_messages(self, messages: List[BaseMessage]) -> str:
        """Extract task description from messages"""
        # Get the last user message as task description
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                content = msg.content if hasattr(msg, 'content') else str(msg)
                # Return first 200 characters
                return content[:200]
        return "General task"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        cache_hit_rate = (self.cache_hits / self.calls_made * 100) if self.calls_made > 0 else 0
        
        return {
            "calls_made": self.calls_made,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "total_cost": self.total_cost,
            "average_cost_per_call": self.total_cost / self.calls_made if self.calls_made > 0 else 0
        }


def get_optimized_llm_client(
    db=None,
    project_id: Optional[str] = None,
    default_model: str = "claude-3-7-sonnet-20250219"
) -> OptimizedLLMClient:
    """Factory function to create optimized LLM client"""
    return OptimizedLLMClient(
        db=db,
        project_id=project_id,
        default_model=default_model
    )
