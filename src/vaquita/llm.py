"""LLM interaction layer — summarises diffs and classifies changes."""

import json

from rich.console import Console

from .llm_providers import Provider, get_client
from .models import ChangeType, Commit, ReleaseSection

console_llm = Console()


def summarise(
    commits: list[Commit],
    diff: str,
    model_provider: Provider,
    model_name: str,
) -> list[ReleaseSection]:
    """Given commits and a diff, return structured release sections."""
    llm = get_client(provider=model_provider, model=model_name)

    prompt = f"""
        Summarise the following git diff and commits into clear, concise release notes.
        Focus on user-facing changes, group similar changes together, and use bullet points.
        Respond with only valid JSON matching this schema — no markdown fences, no extra text:

        {{
            "sections": [
                {{
                    "title": "string",
                    "changes": ["string"]
                }}
            ]
        }}

        Commits:
        {commits}

        Diff:
        {diff}
    """

    raw = llm(prompt)
    console_llm.print(raw)

    parsed = json.loads(raw)
    sections: list[ReleaseSection] = []
    for section in parsed.get("sections", []):
        # Map the free-form title to a ChangeType best-effort
        title = section.get("title", "").lower()
        change_type = _infer_change_type(title)
        sections.append(ReleaseSection(change_type=change_type, entries=section.get("changes", [])))

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
    if any(w in title for w in ("chore", "refactor", "ci", "build", "dep")):
        return ChangeType.CHORE
    return ChangeType.UNKNOWN
