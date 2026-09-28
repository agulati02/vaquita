"""LLM interaction layer — summarises diffs and classifies changes."""

from .models import Commit, ReleaseSection


def summarise(commits: list[Commit], diff: str) -> list[ReleaseSection]:
    """Given commits and a diff, return structured release sections."""
    raise NotImplementedError
