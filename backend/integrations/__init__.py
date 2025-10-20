"""
Integrations Module
External service integrations (GitHub, etc.)
"""

from integrations.github_integration import GitHubIntegrationService, get_github_service

__all__ = ['GitHubIntegrationService', 'get_github_service']
