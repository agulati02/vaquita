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


def get_diff(
    repo_path: Path,
    from_ref: str,
    to_ref: str,
    path: str | None = None,
    paths: list[str] | None = None,
) -> str:
    """Return the unified diff between from_ref and to_ref, optionally scoped to file(s)."""
    repo = git.Repo(repo_path)
    targets: list[str] = []
    if path:
        targets = [path]
    elif paths:
        targets = paths
    if targets:
        return repo.git.diff(from_ref, to_ref, "--", *targets)
    return repo.git.diff(from_ref, to_ref)


def _classify_path(path: str) -> str:
    from fnmatch import fnmatch
    rules = [
        ("lock",      ["*.lock", "package-lock.json", "yarn.lock", "Cargo.lock", "poetry.lock"]),
        ("vendor",    ["*/vendor/*", "*/node_modules/*", "*/third_party/*"]),
        ("generated", ["*/__pycache__/*", "*.pb.go", "*.pb.py", "*_generated.*", "*/.next/*"]),
        ("test",      ["*/test/*", "*/tests/*", "*/__tests__/*", "*_test.*", "*_spec.*", "*.test.*", "*.spec.*"]),
        ("docs",      ["*.md", "*.rst", "*.txt", "docs/*"]),
        ("config",    ["*.toml", "*.yaml", "*.yml", "*.json", "*.ini", "*.cfg", "Dockerfile", "*.env", "*.env.*"]),
    ]
    for tag, patterns in rules:
        if any(fnmatch(path, p) or fnmatch(path.split("/")[-1], p) for p in patterns):
            return tag
    return "source"


def list_changed_files(repo_path: Path, from_ref: str, to_ref: str) -> str:
    repo = git.Repo(repo_path)
    diff_index = repo.commit(to_ref).diff(repo.commit(from_ref))
    lines = []
    for d in diff_index:
        path = d.b_path or d.a_path
        stat = repo.git.diff("--numstat", from_ref, to_ref, "--", path)
        if stat:
            parts = stat.split("\t")
            added, removed = parts[0], parts[1]
            tag = _classify_path(path)
            lines.append(f"{path:<60} +{added:<6} -{removed:<6} [{tag}]")
    return "\n".join(lines)


def get_commit_detail(repo_path: Path, sha: str) -> str:
    repo = git.Repo(repo_path)
    commit = repo.commit(sha)
    diff = repo.git.diff(f"{sha}^", sha)
    return f"{commit.message.strip()}\n\n{diff}"
