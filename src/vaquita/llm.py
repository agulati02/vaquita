"""LLM interaction layer — summarises diffs and classifies changes."""

from .models import Commit, ReleaseSection


def summarise(commits: list[Commit], diff: str, model_provider: str, model_name: str) -> list[ReleaseSection]:
    """Given commits and a diff, return structured release sections."""
    raise NotImplementedError
