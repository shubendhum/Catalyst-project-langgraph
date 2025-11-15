"""
Configuration Router
Allows dynamic configuration of LLM settings and agent parameters
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import os

router = APIRouter(prefix="/config", tags=["config"])
logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """LLM configuration model"""
    model: str = Field(..., description="Model name (e.g., gpt-4, claude-3-opus)")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for sampling")
    max_tokens: int = Field(4096, ge=1, le=100000, description="Maximum tokens to generate")
    router_policy: str = Field("smart", description="Router policy: smart, cost, performance, quality")
    provider: Optional[str] = Field(None, description="Provider override: openai, anthropic, google")


class AgentConfig(BaseModel):
    """Agent configuration model"""
    max_concurrent_tasks: int = Field(5, ge=1, le=20)
    agent_timeout: int = Field(300, ge=30, le=3600)
    enable_cost_optimizer: bool = True
    enable_learning_service: bool = True
    enable_context_manager: bool = True


class SystemConfig(BaseModel):
    """Complete system configuration"""
    llm: LLMConfig
    agent: AgentConfig


# Global configuration storage (in-memory for now)
_current_config: Dict[str, Any] = {
    "llm": {
        "model": os.getenv("DEFAULT_LLM_MODEL", "claude-3-7-sonnet-20250219"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
        "router_policy": os.getenv("ROUTER_POLICY", "smart"),
        "provider": os.getenv("DEFAULT_LLM_PROVIDER", "emergent")
    },
    "agent": {
        "max_concurrent_tasks": int(os.getenv("MAX_CONCURRENT_TASKS", "5")),
        "agent_timeout": int(os.getenv("AGENT_TIMEOUT", "300")),
        "enable_cost_optimizer": os.getenv("ENABLE_COST_OPTIMIZER", "true").lower() == "true",
        "enable_learning_service": os.getenv("ENABLE_LEARNING_SERVICE", "true").lower() == "true",
        "enable_context_manager": os.getenv("ENABLE_CONTEXT_MANAGER", "true").lower() == "true"
    }
}


@router.get("/", response_model=SystemConfig)
async def get_config():
    """
    Get current system configuration
    
    Returns LLM and agent settings currently in use.
    """
    try:
        return SystemConfig(**_current_config)
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm")
async def get_llm_config():
    """Get current LLM configuration"""
    return _current_config["llm"]


@router.post("/llm")
async def update_llm_config(config: LLMConfig):
    """
    Update LLM configuration
    
    Example:
        POST /api/config/llm
        {
            "model": "gpt-4-turbo",
            "temperature": 0.8,
            "max_tokens": 8192,
            "router_policy": "performance",
            "provider": "openai"
        }
    """
    try:
        # Update in-memory config
        _current_config["llm"] = config.dict()
        
        logger.info(f"LLM config updated: {config.dict()}")
        
        return {
            "message": "LLM configuration updated successfully",
            "config": _current_config["llm"]
        }
    except Exception as e:
        logger.error(f"Failed to update LLM config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent")
async def get_agent_config():
    """Get current agent configuration"""
    return _current_config["agent"]


@router.post("/agent")
async def update_agent_config(config: AgentConfig):
    """
    Update agent configuration
    
    Example:
        POST /api/config/agent
        {
            "max_concurrent_tasks": 10,
            "agent_timeout": 600,
            "enable_cost_optimizer": true
        }
    """
    try:
        # Update in-memory config
        _current_config["agent"] = config.dict()
        
        logger.info(f"Agent config updated: {config.dict()}")
        
        return {
            "message": "Agent configuration updated successfully",
            "config": _current_config["agent"]
        }
    except Exception as e:
        logger.error(f"Failed to update agent config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_config():
    """
    Reset configuration to defaults from environment variables
    """
    global _current_config
    
    _current_config = {
        "llm": {
            "model": os.getenv("DEFAULT_LLM_MODEL", "claude-3-7-sonnet-20250219"),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
            "router_policy": os.getenv("ROUTER_POLICY", "smart"),
            "provider": os.getenv("DEFAULT_LLM_PROVIDER", "emergent")
        },
        "agent": {
            "max_concurrent_tasks": int(os.getenv("MAX_CONCURRENT_TASKS", "5")),
            "agent_timeout": int(os.getenv("AGENT_TIMEOUT", "300")),
            "enable_cost_optimizer": os.getenv("ENABLE_COST_OPTIMIZER", "true").lower() == "true",
            "enable_learning_service": os.getenv("ENABLE_LEARNING_SERVICE", "true").lower() == "true",
            "enable_context_manager": os.getenv("ENABLE_CONTEXT_MANAGER", "true").lower() == "true"
        }
    }
    
    return {
        "message": "Configuration reset to defaults",
        "config": _current_config
    }


@router.get("/models")
async def get_available_models():
    """
    Get list of available LLM models
    
    Returns models grouped by provider.
    """
    return {
        "openai": [
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000},
            {"id": "gpt-4", "name": "GPT-4", "context_window": 8192},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_window": 16385}
        ],
        "anthropic": [
            {"id": "claude-3-7-sonnet-20250219", "name": "Claude 3.7 Sonnet", "context_window": 200000},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_window": 200000},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_window": 200000}
        ],
        "google": [
            {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash", "context_window": 1000000},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context_window": 2000000}
        ]
    }


@router.get("/router-policies")
async def get_router_policies():
    """
    Get available router policies
    
    Router policies determine how the system selects models.
    """
    return {
        "policies": [
            {
                "id": "smart",
                "name": "Smart",
                "description": "Balances cost, performance, and quality based on task complexity"
            },
            {
                "id": "cost",
                "name": "Cost-Optimized",
                "description": "Prioritizes lowest cost models while maintaining acceptable quality"
            },
            {
                "id": "performance",
                "name": "Performance",
                "description": "Prioritizes fastest response times"
            },
            {
                "id": "quality",
                "name": "Quality",
                "description": "Uses best available models regardless of cost"
            }
        ]
    }


def get_current_config() -> Dict[str, Any]:
    """
    Get current configuration (for internal use)
    
    Returns:
        Current system configuration
    """
    return _current_config
