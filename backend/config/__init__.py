"""
Configuration Module
Handles environment detection and configuration management
"""

from config.environment import (
    detect_environment,
    get_environment_config,
    get_config,
    is_docker_desktop,
    is_kubernetes,
    get_orchestration_mode,
    should_use_postgres,
    should_use_events,
    should_use_git,
    should_use_preview
)

__all__ = [
    'detect_environment',
    'get_environment_config',
    'get_config',
    'is_docker_desktop',
    'is_kubernetes',
    'get_orchestration_mode',
    'should_use_postgres',
    'should_use_events',
    'should_use_git',
    'should_use_preview'
]
