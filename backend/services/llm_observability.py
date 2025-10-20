"""
LLM Observability Service
Dual-mode: Langfuse (Docker Desktop) + Langsmith (K8s)
Provides tracing, logging, and monitoring for all LLM calls
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from config.environment import is_docker_desktop, is_kubernetes

logger = logging.getLogger(__name__)


class LLMObservabilityService:
    """
    Handles LLM observability:
    - Langfuse in Docker Desktop (self-hosted)
    - Langsmith in K8s (cloud-based)
    - Automatic environment detection
    """
    
    def __init__(self):
        self.environment = "docker_desktop" if is_docker_desktop() else "kubernetes"
        self.langfuse_enabled = False
        self.langsmith_enabled = False
        
        # Initialize Langfuse (Docker Desktop)
        if is_docker_desktop():
            self._init_langfuse()
        
        # Initialize Langsmith (K8s or if explicitly enabled)
        if is_kubernetes() or os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
            self._init_langsmith()
        
        logger.info(
            f"✅ LLM Observability: "
            f"Langfuse={self.langfuse_enabled}, "
            f"Langsmith={self.langsmith_enabled}"
        )
    
    def _init_langfuse(self):
        """Initialize Langfuse (self-hosted)"""
        try:
            from langfuse import Langfuse
            
            # Check if Langfuse is configured
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            host = os.getenv("LANGFUSE_HOST", "http://langfuse:3000")
            
            # If keys not set, Langfuse will auto-generate on first login
            # We can still initialize the client
            self.langfuse = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            
            self.langfuse_enabled = True
            logger.info(f"✅ Langfuse initialized: {host}")
            
        except ImportError:
            logger.warning("Langfuse not installed. Install: pip install langfuse")
            self.langfuse_enabled = False
        except Exception as e:
            logger.warning(f"Langfuse initialization failed: {e}")
            self.langfuse_enabled = False
    
    def _init_langsmith(self):
        """Initialize Langsmith (cloud)"""
        try:
            # Langsmith uses environment variables automatically
            api_key = os.getenv("LANGCHAIN_API_KEY")
            tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
            
            if tracing_enabled and api_key:
                # LangChain automatically traces when these are set
                self.langsmith_enabled = True
                project = os.getenv("LANGCHAIN_PROJECT", "catalyst")
                logger.info(f"✅ Langsmith tracing enabled (project: {project})")
            else:
                logger.info("Langsmith not configured (set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY)")
                
        except Exception as e:
            logger.warning(f"Langsmith initialization failed: {e}")
            self.langsmith_enabled = False
    
    def trace_llm_call(
        self,
        name: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict] = None,
        task_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ):
        """
        Trace an LLM call
        Routes to Langfuse or Langsmith based on environment
        """
        
        if self.langfuse_enabled:
            self._trace_langfuse(name, input_data, output_data, metadata, task_id, agent_name)
        
        # Langsmith traces automatically if configured
        # Just ensure environment variables are set
    
    def _trace_langfuse(
        self,
        name: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict],
        task_id: Optional[str],
        agent_name: Optional[str]
    ):
        """Send trace to Langfuse"""
        try:
            # Create trace
            trace = self.langfuse.trace(
                name=name,
                metadata={
                    "task_id": task_id,
                    "agent": agent_name,
                    "environment": self.environment,
                    **(metadata or {})
                }
            )
            
            # Add generation
            trace.generation(
                name=f"{agent_name or 'agent'}_llm_call",
                input=input_data,
                output=output_data,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to trace to Langfuse: {e}")
    
    def create_session(self, task_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Create an observability session for a task
        Returns session ID
        """
        if self.langfuse_enabled:
            try:
                session_id = f"task-{task_id}"
                
                # Langfuse will automatically group traces by session
                return session_id
                
            except Exception as e:
                logger.error(f"Failed to create Langfuse session: {e}")
                return None
        
        return None
    
    def log_agent_execution(
        self,
        task_id: str,
        agent_name: str,
        input_data: Dict,
        output_data: Dict,
        duration_seconds: float,
        cost: float = 0.0,
        tokens: int = 0
    ):
        """Log complete agent execution"""
        
        if self.langfuse_enabled:
            try:
                self.langfuse.trace(
                    name=f"{agent_name}_execution",
                    session_id=f"task-{task_id}",
                    metadata={
                        "task_id": task_id,
                        "agent": agent_name,
                        "duration": duration_seconds,
                        "cost": cost,
                        "tokens": tokens
                    },
                    input=input_data,
                    output=output_data
                )
            except Exception as e:
                logger.error(f"Failed to log to Langfuse: {e}")
    
    def flush(self):
        """Flush pending traces"""
        if self.langfuse_enabled:
            try:
                self.langfuse.flush()
            except:
                pass
    
    def get_dashboard_url(self) -> Optional[str]:
        """Get observability dashboard URL"""
        if self.langfuse_enabled:
            return "http://localhost:3001"
        elif self.langsmith_enabled:
            return "https://smith.langchain.com"
        return None


# Singleton instance
_observability_service = None


def get_observability_service() -> LLMObservabilityService:
    """Get or create LLMObservabilityService singleton"""
    global _observability_service
    if _observability_service is None:
        _observability_service = LLMObservabilityService()
    return _observability_service


# Decorator for automatic tracing
def trace_llm_call(func):
    """Decorator to automatically trace LLM calls"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        obs_service = get_observability_service()
        
        # Extract metadata
        agent_name = kwargs.get('agent_name')
        task_id = kwargs.get('task_id')
        
        # Execute function
        result = await func(*args, **kwargs)
        
        # Trace
        obs_service.trace_llm_call(
            name=func.__name__,
            input_data=kwargs,
            output_data=result,
            metadata={},
            task_id=task_id,
            agent_name=agent_name
        )
        
        return result
    
    return wrapper
