from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlparse, urlunparse


class GitHubConfigError(RuntimeError):
    """Raised when mandatory GitHub configuration is missing."""


class GitCommandError(RuntimeError):
    """Raised when a git command fails."""


@dataclass(slots=True)
class GitHubConfig:
    """
    Configuration holder for GitHub operations.

    Attributes read from environment variables:
        - GITHUB_REPO_URL (required)
        - GITHUB_TOKEN (optional; used if repo URL has no credentials)
        - GITHUB_USERNAME (optional; defaults to token based auth)
        - GITHUB_REMOTE_NAME (defaults to 'origin')
        - GIT_REPO_PATH (defaults to current working directory)
    """

    repo_url: str
    token: str | None
    username: str | None
    remote_name: str
    repo_path: Path
    commit_name: str
    commit_email: str
    commit_identity_explicit: bool

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        raw_repo_url = os.getenv("GITHUB_REPO_URL")
        if not raw_repo_url:
            raise GitHubConfigError(
                "GITHUB_REPO_URL environment variable is required for GitHub operations."
            )

        repo_url = raw_repo_url.strip()
        parsed_repo_url = urlparse(repo_url)

        token = os.getenv("GITHUB_TOKEN")
        username = os.getenv("GITHUB_USERNAME")
        remote_name = os.getenv("GITHUB_REMOTE_NAME", "origin")
        repo_path = Path(os.getenv("GIT_REPO_PATH", ".")).resolve()
        commit_name_env = os.getenv("GITHUB_COMMIT_NAME")
        commit_email_env = os.getenv("GITHUB_COMMIT_EMAIL")

        embedded_username = parsed_repo_url.username or (username.strip() if username else "")

        if not commit_name_env:
            # Prefer configured username; fall back to embedded URL username; default to automation label.
            commit_name = embedded_username or "automation"
        else:
            commit_name = commit_name_env.strip()

        if not commit_email_env:
            base = embedded_username or commit_name.replace(" ", "").lower() or "automation"
            commit_email = f"{base}@users.noreply.github.com"
        else:
            commit_email = commit_email_env.strip()

        return cls(
            repo_url=repo_url,
            token=(token.strip() if token else None),
            username=(username.strip() if username else None),
            remote_name=remote_name.strip(),
            repo_path=repo_path,
            commit_name=commit_name.strip(),
            commit_email=commit_email.strip(),
            commit_identity_explicit=bool(commit_name_env or commit_email_env),
        )

    def authenticated_url(self) -> str:
        """
        Build a repository URL that includes credentials.

        If the configured URL already contains credentials they are reused.
        Otherwise, the method injects username/token into the netloc, using
        either `GITHUB_USERNAME` or the token as the username fallback.
        """

        parsed = urlparse(self.repo_url)

        if parsed.username or parsed.password:
            return self.repo_url

        if not self.token:
            raise GitHubConfigError(
                "GITHUB_TOKEN is required when GITHUB_REPO_URL does not contain credentials."
            )

        username = self.username or "git"
        netloc = f"{username}:{self.token}@{parsed.netloc}"
        return urlunparse(parsed._replace(netloc=netloc))

    def sanitized_url(self) -> str:
        """Return a version of the URL safe to log (credentials removed)."""

        parsed = urlparse(self.authenticated_url())
        if parsed.password:
            netloc = parsed.netloc.split("@")[-1]
            return urlunparse(parsed._replace(netloc=netloc))
        return self.repo_url


class GitHubClient:
    """
    Lightweight helper around `git` CLI for scripted deployments.

    It does not depend on external libraries and relies on the presence of the
    `git` executable in PATH. All commands are executed in the configured repo path.
    """

    def __init__(self, config: GitHubConfig | None = None) -> None:
        self.config = config or GitHubConfig.from_env()

    # --------------------------------------------------------------------- #
    # Git command execution helpers
    # --------------------------------------------------------------------- #
    def _run_git(self, args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess:
        cmd = ["git", *args]
        result = subprocess.run(
            cmd,
            cwd=self.config.repo_path,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise GitCommandError(
                f"Git command failed ({' '.join(cmd)}): {result.stderr.strip() or result.stdout.strip()}"
            )
        return result

    # --------------------------------------------------------------------- #
    # Public operations
    # --------------------------------------------------------------------- #
    def ensure_repository(self) -> None:
        """
        Initialise a repository if the target directory is not under git control.
        """

        if not (self.config.repo_path / ".git").exists():
            self._run_git(["init"])

    def ensure_remote(self) -> None:
        """
        Ensure that the configured remote name points to the authenticated URL.
        """

        remote = self.config.remote_name
        auth_url = self.config.authenticated_url()
        sanitized = self.config.sanitized_url()

        try:
            result = self._run_git(["remote", "get-url", remote], check=False)
            current_url = result.stdout.strip()
        except GitCommandError:
            current_url = ""

        if not current_url:
            self._run_git(["remote", "add", remote, auth_url])
            return

        if sanitized not in current_url and auth_url not in current_url:
            self._run_git(["remote", "set-url", remote, auth_url])

    def _get_git_config(self, key: str) -> str | None:
        """
        Fetch a git configuration value for the local repository.
        """

        result = self._run_git(["config", "--get", key], check=False)
        if result.returncode != 0:
            return None
        value = result.stdout.strip()
        return value or None

    def ensure_identity(self) -> None:
        """
        Configure git committer identity for the repository if missing.
        """

        desired_name = self.config.commit_name
        desired_email = self.config.commit_email
        explicit = self.config.commit_identity_explicit

        current_name = self._get_git_config("user.name")
        current_email = self._get_git_config("user.email")

        if explicit:
            if desired_name:
                self._run_git(["config", "user.name", desired_name])
            if desired_email:
                self._run_git(["config", "user.email", desired_email])
            return

        if current_name and current_email:
            return

        if not desired_name or not desired_email:
            raise GitHubConfigError(
                "Git committer identity requires both GITHUB_COMMIT_NAME and GITHUB_COMMIT_EMAIL or a repo URL embedding credentials."
            )

        if not current_name:
            self._run_git(["config", "user.name", desired_name])

        if not current_email:
            self._run_git(["config", "user.email", desired_email])

    def ensure_clean_submodules(self) -> None:
        """
        Verify that git submodules do not contain uncommitted changes.

        Git refuses to commit when submodules are dirty; we raise an explicit error
        so automation can surface a clear message.
        """

        result = self._run_git(
            ["submodule", "foreach", "--recursive", "git status --porcelain"],
            check=False,
        )

        dirty_output = result.stdout.strip()

        if dirty_output:
            raise GitCommandError(
                "Dirty submodules detected. Commit or stash changes inside each submodule before retrying:\n"
                f"{dirty_output}"
            )

    def _resolve_commit_message(self, message: str | None) -> str:
        """
        Resolve the commit message from the provided argument, environment, or user input.
        """

        if message and message.strip():
            return message.strip()

        env_message = os.getenv("GITHUB_COMMIT_MESSAGE", "").strip()
        if env_message:
            return env_message

        try:
            prompt = os.getenv("GITHUB_COMMIT_PROMPT", "Commit message")
            resolved = input(f"{prompt}: ").strip()
        except EOFError as exc:
            raise GitCommandError("Commit message is required but could not be read from STDIN.") from exc

        if not resolved:
            raise GitCommandError("Commit message is required. Aborting commit.")

        return resolved

    def ensure_branch(self, branch: str) -> None:
        """
        Ensure that the repository is on the desired branch, creating it if necessary.
        """

        branch = branch.strip()
        if not branch:
            return

        status = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=False)
        current = status.stdout.strip() if status.returncode == 0 else ""

        if current == branch:
            return

        # Create or reset branch to current HEAD (similar to git checkout -B)
        self._run_git(["checkout", "-B", branch], check=False)

    def add(self, paths: Iterable[str] | None = None) -> None:
        """
        Stage files for commit. By default stages all tracked/untracked files.
        """

        args = ["add"]
        if paths:
            args.extend(paths)
        else:
            args.append("--all")
        self._run_git(args)

    def commit(self, message: str) -> bool:
        """
        Create a commit with the provided message.

        Returns:
            bool: True if a commit was created, False if there was nothing to commit.
        """

        result = self._run_git(["commit", "-m", message], check=False)
        if result.returncode != 0:
            combined = (result.stderr or "") + (result.stdout or "")
            if "nothing to commit" in combined.lower():
                return False
            raise GitCommandError(
                f"git commit failed: {combined.strip() or result.returncode}"
            )
        return True

    def push(self, branch: str | None = None, *, set_upstream: bool = True) -> None:
        """
        Push commits to the configured remote.

        Args:
            branch: branch name (default: current branch)
            set_upstream: whether to set upstream tracking on first push
        """

        remote = self.config.remote_name
        args = ["push", remote]
        if branch:
            args.append(branch)
            if set_upstream:
                args.insert(1, "-u")

        self._run_git(args)

    def commit_and_push(
        self,
        message: str | None = None,
        *,
        paths: Iterable[str] | None = None,
        branch: str | None = None,
    ) -> None:
        """
        Convenience helper to stage, commit, and push in one call.
        """

        self.ensure_repository()
        self.ensure_identity()
        self.ensure_remote()
        self.ensure_clean_submodules()
        self.add(paths)
        resolved_message = self._resolve_commit_message(message)
        committed = self.commit(resolved_message)
        if not committed:
            return
        self.push(branch=branch)


