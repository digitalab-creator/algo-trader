"""
GitHub utilities for automated repository operations.

Expose a high-level client that reads configuration from environment
variables (`GITHUB_REPO_URL`, `GITHUB_TOKEN`, etc.) and can be used
by scripts or services that need to push code or manage remotes.
"""

from .client import GitCommandError, GitHubClient, GitHubConfig, GitHubConfigError

__all__ = ["GitHubClient", "GitHubConfig", "GitHubConfigError", "GitCommandError"]


