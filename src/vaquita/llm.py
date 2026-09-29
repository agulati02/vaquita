"""LLM interaction layer — summarises diffs and classifies changes."""

import json
from pathlib import Path

from rich.console import Console

from .llm_providers import Provider, get_client
from .models import ChangeType, Commit, ReleaseSection

console_llm = Console()

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


def summarise(
    commits: list[Commit],
    diff: str,
    model_provider: Provider,
    model_name: str,
) -> list[ReleaseSection]:
    """Given commits and a diff, return structured release sections."""
    system_prompt = _load_prompt("system.prompt")
    user_prompt = _load_prompt("summarise.prompt").format(
        commits=commits,
        diff=diff,
    )

    llm = get_client(provider=model_provider, model=model_name, system_prompt=system_prompt)
    raw = llm(user_prompt)
    console_llm.print(raw)

    parsed = json.loads(raw)
    sections: list[ReleaseSection] = []
    for section in parsed.get("sections", []):
        title = section.get("title", "").lower()
        change_type = _infer_change_type(title)
        sections.append(
            ReleaseSection(change_type=change_type, entries=section.get("changes", []))
        )

    return sections


def _infer_change_type(title: str) -> ChangeType:
    if any(w in title for w in ("break", "incompatible", "removal")):
        return ChangeType.BREAKING
    if any(w in title for w in ("feat", "add", "new")):
        return ChangeType.FEATURE
    if any(w in title for w in ("fix", "bug", "patch", "correct")):
        return ChangeType.FIX
    if any(w in title for w in ("doc", "readme", "changelog")):
        return ChangeType.DOCS
    if any(w in title for w in ("chore", "refactor", "ci", "build", "dep", "maintenance")):
        return ChangeType.CHORE
    return ChangeType.UNKNOWN
