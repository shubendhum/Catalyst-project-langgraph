"""
Prompt Loader Utility
Loads versioned prompt files for agents
"""
import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Cache for loaded prompts
_prompt_cache: Dict[str, str] = {}

# Prompt directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def get_prompt(prompt_name: str, cache: bool = True) -> str:
    """
    Load a prompt by name (with optional version).
    
    Args:
        prompt_name: Prompt name, e.g. "planner_v1", "coder_v2"
        cache: Whether to cache the prompt in memory (default: True)
        
    Returns:
        Prompt text as string
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        
    Example:
        >>> prompt = get_prompt("planner_v1")
        >>> print(prompt)
    """
    # Check cache first
    if cache and prompt_name in _prompt_cache:
        return _prompt_cache[prompt_name]
    
    # Build file path
    prompt_file = PROMPTS_DIR / f"{prompt_name}.md"
    
    if not prompt_file.exists():
        error_msg = f"Prompt file not found: {prompt_file}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        # Load prompt text
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        
        # Cache if requested
        if cache:
            _prompt_cache[prompt_name] = prompt_text
        
        logger.info(f"Loaded prompt: {prompt_name} ({len(prompt_text)} chars)")
        return prompt_text
        
    except Exception as e:
        logger.error(f"Failed to load prompt {prompt_name}: {e}")
        raise


def get_prompt_with_fallback(prompt_name: str, fallback: str = "") -> str:
    """
    Load a prompt with fallback to a default value if file doesn't exist.
    
    Args:
        prompt_name: Prompt name
        fallback: Fallback text if prompt file doesn't exist
        
    Returns:
        Prompt text or fallback
    """
    try:
        return get_prompt(prompt_name)
    except FileNotFoundError:
        logger.warning(f"Prompt {prompt_name} not found, using fallback")
        return fallback


def list_prompts() -> list:
    """
    List all available prompts
    
    Returns:
        List of prompt names (without .md extension)
    """
    if not PROMPTS_DIR.exists():
        return []
    
    prompts = []
    for prompt_file in PROMPTS_DIR.glob("*.md"):
        prompt_name = prompt_file.stem
        prompts.append(prompt_name)
    
    return sorted(prompts)


def clear_cache():
    """Clear the prompt cache"""
    global _prompt_cache
    _prompt_cache.clear()
    logger.info("Prompt cache cleared")


def reload_prompt(prompt_name: str) -> str:
    """
    Reload a prompt from disk, bypassing cache
    
    Args:
        prompt_name: Prompt name
        
    Returns:
        Fresh prompt text
    """
    # Remove from cache if present
    _prompt_cache.pop(prompt_name, None)
    
    # Load fresh
    return get_prompt(prompt_name, cache=True)


def get_prompt_metadata(prompt_name: str) -> Dict[str, any]:
    """
    Get metadata about a prompt
    
    Args:
        prompt_name: Prompt name
        
    Returns:
        Dictionary with metadata (file_size, version, etc.)
    """
    prompt_file = PROMPTS_DIR / f"{prompt_name}.md"
    
    if not prompt_file.exists():
        return {"exists": False}
    
    stat = prompt_file.stat()
    
    # Extract version from name (e.g., "planner_v1" -> "v1")
    version = None
    if "_v" in prompt_name:
        version = prompt_name.split("_v")[-1]
    
    return {
        "exists": True,
        "path": str(prompt_file),
        "size_bytes": stat.st_size,
        "modified_time": stat.st_mtime,
        "version": version,
        "cached": prompt_name in _prompt_cache
    }


# Convenience functions for common prompts
def get_planner_prompt(version: int = 1) -> str:
    """Get planner prompt"""
    return get_prompt(f"planner_v{version}")


def get_architect_prompt(version: int = 1) -> str:
    """Get architect prompt"""
    return get_prompt(f"architect_v{version}")


def get_coder_prompt(version: int = 1) -> str:
    """Get coder prompt"""
    return get_prompt(f"coder_v{version}")


def get_tester_prompt(version: int = 1) -> str:
    """Get tester prompt"""
    return get_prompt(f"tester_v{version}")


def get_reviewer_prompt(version: int = 1) -> str:
    """Get reviewer prompt"""
    return get_prompt(f"reviewer_v{version}")


def get_deployer_prompt(version: int = 1) -> str:
    """Get deployer prompt"""
    return get_prompt(f"deployer_v{version}")


def get_explorer_prompt(version: int = 1) -> str:
    """Get explorer prompt"""
    return get_prompt(f"explorer_v{version}")
