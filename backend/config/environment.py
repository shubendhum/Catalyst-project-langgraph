"""
Environment Detection and Configuration
Automatically detects K8s vs Docker Desktop and configures accordingly
"""
import os
from typing import Literal, Dict, Any
from pathlib import Path

EnvironmentType = Literal["kubernetes", "docker_desktop"]


def detect_environment() -> EnvironmentType:
    """
    Auto-detect current environment
    
    Returns:
        "docker_desktop" if running in Docker Desktop with full infrastructure
        "kubernetes" if running in K8s pod (Emergent platform)
    """
    
    # Check for Docker socket (indicates Docker Desktop)
    if os.path.exists("/var/run/docker.sock"):
        return "docker_desktop"
    
    # Check for Docker environment file
    if os.path.exists("/.dockerenv"):
        return "docker_desktop"
    
    # Check if running in K8s pod
    if os.path.exists("/var/run/secrets/kubernetes.io"):
        return "kubernetes"
    
    # Check for supervisor (K8s indicator)
    if os.path.exists("/etc/supervisor/conf.d"):
        return "kubernetes"
    
    # Default to kubernetes for safety (simpler fallback)
    return "kubernetes"


def get_environment_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration
    """
    env = detect_environment()
    
    if env == "docker_desktop":
        return {
            "environment": "docker_desktop",
            "orchestration_mode": "event_driven",
            "databases": {
                "postgres": {
                    "enabled": True,
                    "url": os.getenv("POSTGRES_URL", "postgresql://catalyst:catalyst_state_2025@postgres:5432/catalyst_state")
                },
                "mongodb": {
                    "enabled": True,
                    "url": os.getenv("MONGO_URL", "mongodb://admin:catalyst_admin_pass@mongodb:27017")
                },
                "redis": {
                    "enabled": True,
                    "url": os.getenv("REDIS_URL", "redis://redis:6379")
                },
                "qdrant": {
                    "enabled": True,
                    "url": os.getenv("QDRANT_URL", "http://qdrant:6333")
                }
            },
            "event_streaming": {
                "enabled": True,
                "provider": "rabbitmq",
                "url": os.getenv("RABBITMQ_URL", "amqp://catalyst:catalyst_queue_2025@rabbitmq:5672/catalyst")
            },
            "git": {
                "enabled": True,
                "mode": os.getenv("GIT_STORAGE_MODE", "both"),  # local, github, both
                "local_path": "/app/repos",
                "github_token": os.getenv("GITHUB_TOKEN"),
                "github_org": os.getenv("GITHUB_ORG", "catalyst-generated")
            },
            "preview": {
                "enabled": True,
                "mode": os.getenv("PREVIEW_MODE", "docker_in_docker"),  # docker_in_docker, compose_only, traefik
                "port_range": [9000, 9999],
                "auto_cleanup_hours": 24,
                "traefik_base_domain": "localhost"
            },
            "artifacts": {
                "path": "/app/artifacts",
                "retention_days": 30
            }
        }
    
    else:  # kubernetes
        return {
            "environment": "kubernetes",
            "orchestration_mode": "sequential",
            "databases": {
                "postgres": {
                    "enabled": False  # Not available in K8s
                },
                "mongodb": {
                    "enabled": True,
                    "url": os.getenv("MONGO_URL", "mongodb://localhost:27017")
                },
                "redis": {
                    "enabled": False,  # Fallback to in-memory
                    "fallback": "memory"
                },
                "qdrant": {
                    "enabled": False,  # Fallback to in-memory
                    "fallback": "memory"
                }
            },
            "event_streaming": {
                "enabled": False,  # No RabbitMQ in K8s
                "fallback": "direct_calls"
            },
            "git": {
                "enabled": False,  # No Git in K8s pod
                "mode": "filesystem",
                "local_path": "/app/generated_projects"
            },
            "preview": {
                "enabled": False,  # No Docker available
                "mode": "none"
            },
            "artifacts": {
                "path": "/app/generated_projects",  # Simpler path
                "retention_days": 7
            }
        }


# Singleton instance
_config = None


def get_config() -> Dict[str, Any]:
    """Get or create configuration singleton"""
    global _config
    if _config is None:
        _config = get_environment_config()
    return _config


def is_docker_desktop() -> bool:
    """Check if running in Docker Desktop"""
    return get_config()["environment"] == "docker_desktop"


def is_kubernetes() -> bool:
    """Check if running in Kubernetes"""
    return get_config()["environment"] == "kubernetes"


def get_orchestration_mode() -> Literal["sequential", "event_driven"]:
    """Get orchestration mode based on environment"""
    return get_config()["orchestration_mode"]


# Convenience functions
def should_use_postgres() -> bool:
    return get_config()["databases"]["postgres"]["enabled"]


def should_use_events() -> bool:
    return get_config()["event_streaming"]["enabled"]


def should_use_git() -> bool:
    return get_config()["git"]["enabled"]


def should_use_preview() -> bool:
    return get_config()["preview"]["enabled"]


if __name__ == "__main__":
    # Test environment detection
    config = get_config()
    print(f"Environment: {config['environment']}")
    print(f"Orchestration Mode: {config['orchestration_mode']}")
    print(f"Postgres: {config['databases']['postgres']['enabled']}")
    print(f"Git: {config['git']['enabled']}")
    print(f"Preview: {config['preview']['enabled']}")
