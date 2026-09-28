"""Git interaction layer — fetches commits, diffs, and PR metadata."""

from pathlib import Path

from .models import Commit


def get_commits(repo_path: Path, from_ref: str, to_ref: str) -> list[Commit]:
    """Return commits reachable from to_ref but not from_ref."""
    raise NotImplementedError


def get_diff(repo_path: Path, from_ref: str, to_ref: str) -> str:
    """Return the unified diff between from_ref and to_ref."""
    raise NotImplementedError
