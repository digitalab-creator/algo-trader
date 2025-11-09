"""
Shared infrastructure for algo-trading services.

Provides centralized setup for database, logging, monitoring, and more.
"""

from lib.infrastructure.context import AppContext
from lib.infrastructure.github import GitHubClient, GitHubConfig, GitHubConfigError, GitCommandError
from lib.infrastructure.setup import setup_app

__all__ = [
    "setup_app",
    "AppContext",
    "GitHubClient",
    "GitHubConfig",
    "GitHubConfigError",
    "GitCommandError",
]

