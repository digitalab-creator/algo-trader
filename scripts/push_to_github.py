"""
Automate staging, testing, committing, and pushing changes to GitHub.

Reads configuration from the environment (see env.example) and relies on the
GitHub infrastructure helpers to configure remotes and authentication.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


REPO_PATH = Path(__file__).resolve().parents[1]
if str(REPO_PATH) not in sys.path:
    sys.path.append(str(REPO_PATH))

from lib.infrastructure.github import (  # noqa: E402
    GitHubClient,
    GitHubConfigError,
    GitCommandError,
)


load_dotenv()

UNIT_TEST_COMMAND = os.getenv("UNIT_TEST_COMMAND", "").strip()
INTEGRATION_TEST_COMMAND = os.getenv("INTEGRATION_TEST_COMMAND", "").strip()
GIT_AUTHOR_NAME = os.getenv("GIT_AUTHOR_NAME", "").strip()
GIT_AUTHOR_EMAIL = os.getenv("GIT_AUTHOR_EMAIL", "").strip()
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "dev").strip() or "dev"


def run_shell(command: str, description: str) -> None:
    """Run a shell command, raising on failure."""

    print(f"⚓ {description}")
    result = subprocess.run(
        command,
        cwd=REPO_PATH,
        shell=True,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())

    if result.returncode != 0:
        raise RuntimeError(
            f"Command '{command}' failed with exit code {result.returncode}"
        )


def run_optional_tests(command: str, label: str) -> None:
    """Execute optional test command if provided."""

    if not command:
        print(f"⏭️  Skipping {label}; no command configured.")
        return
    run_shell(command, f"Running {label}")


def configure_git_identity(name: str, email: str) -> None:
    """Configure local git author information if provided."""

    if name:
        run_shell(f'git config user.name {shlex.quote(name)}', "Setting git author name")
    if email:
        run_shell(f'git config user.email {shlex.quote(email)}', "Setting git author email")


def ask_commit_message() -> str:
    try:
        return input("📝 Commit message: ").strip()
    except KeyboardInterrupt:
        print("\n🚫 Commit aborted by user.")
        sys.exit(1)


def main() -> None:
    try:
        client = GitHubClient()
    except GitHubConfigError as exc:
        print(f"⚠️  Missing configuration: {exc}")
        sys.exit(1)

    try:
        client.config.repo_path = REPO_PATH
        client.ensure_repository()
        client.ensure_remote()
        client.ensure_branch(GITHUB_BRANCH)
        print(f"✅ Remote configured: {client.config.remote_name} -> {client.config.sanitized_url()}")

        # Configure git author identity if provided.
        configure_git_identity(GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL)

        # Run tests before committing.
        run_optional_tests(UNIT_TEST_COMMAND, "unit tests")
        run_optional_tests(INTEGRATION_TEST_COMMAND, "integration tests")

        message = ask_commit_message()
        if not message:
            print("⚠️  Commit message is required. Aborting.")
            sys.exit(1)

        client.add()
        committed = client.commit(message)
        if not committed:
            print("ℹ️  Nothing to commit. Skipping push.")
            return

        client.push(branch=GITHUB_BRANCH)
        print(f"🎉 Changes committed and pushed to {GITHUB_BRANCH}.")

    except (GitCommandError, RuntimeError) as exc:
        print(f"💥 Git operation failed: {exc}")
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"💥 Unexpected error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()


