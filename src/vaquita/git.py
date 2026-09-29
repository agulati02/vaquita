"""Git interaction layer — fetches commits, diffs, and PR metadata."""

import git
from pathlib import Path

from .models import Commit


def get_commits(repo_path: Path, from_ref: str, to_ref: str) -> list[Commit]:
    """Return commits reachable from to_ref but not from_ref."""
    def to_commit_dto(c: git.Commit) -> Commit:
        return Commit(
            sha=c.hexsha,
            message=c.message,
            author=c.author.name,
            email=c.author.email,
            timestamp=str(c.committed_datetime),
        )
    repo = git.Repo(repo_path)
    commits = list(repo.iter_commits(f"{from_ref}..{to_ref}"))
    return [to_commit_dto(c) for c in commits]


def get_diff(repo_path: Path, from_ref: str, to_ref: str) -> str:
    """Return the unified diff between from_ref and to_ref."""
    repo = git.Repo(repo_path)
    return repo.git.diff(from_ref, to_ref)
