"""Orchestrates the release note generation pipeline."""

from .config import Config
from .git import get_commits, get_diff
from .llm import summarise
from .models import ReleaseNotes


def generate_notes(config: Config) -> ReleaseNotes:
    """Run the full pipeline: fetch → summarise → return structured notes."""
    commits = get_commits(config.repo_path, config.from_ref, config.to_ref)
    diff = get_diff(config.repo_path, config.from_ref, config.to_ref)
    sections = summarise(commits, diff, config.model_provider, config.model_name)
    return ReleaseNotes(
        from_ref=config.from_ref,
        to_ref=config.to_ref,
        sections=sections,
        commits=commits,
    )
