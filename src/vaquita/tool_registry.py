from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .git import get_commits, get_diff, list_changed_files, get_commit_detail


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., str]


class ToolRegistry:
    def __init__(self, repo_path: Path, from_ref: str, to_ref: str) -> None:
        self._repo_path = repo_path
        self._from_ref = from_ref
        self._to_ref = to_ref
        self._tools: dict[str, ToolDef] = {}
        self._register()

    def _register(self) -> None:
        repo, fr, to = self._repo_path, self._from_ref, self._to_ref

        def _get_commits(from_ref: str = fr, to_ref: str = to) -> str:
            commits = get_commits(repo, from_ref, to_ref)
            lines = [
                f"{c.sha[:8]} {c.timestamp} {c.author} — {c.message.splitlines()[0]}"
                for c in commits
            ]
            return "\n".join(lines)

        def _list_changed_files(from_ref: str = fr, to_ref: str = to) -> str:
            return list_changed_files(repo, from_ref, to_ref)

        def _get_file_diff(path: str, from_ref: str = fr, to_ref: str = to) -> str:
            return get_diff(repo, from_ref, to_ref, path=path)

        def _get_diff_for_paths(paths: list[str], from_ref: str = fr, to_ref: str = to) -> str:
            return get_diff(repo, from_ref, to_ref, paths=paths)

        def _get_commit_detail(sha: str) -> str:
            return get_commit_detail(repo, sha)

        defs = [
            ToolDef(
                name="get_commits",
                description=(
                    "Return a compact list of commits between from_ref and to_ref. "
                    "Each line: <sha_short> <timestamp> <author> — <message_first_line>. "
                    "Call this first to get the full commit inventory."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "from_ref": {"type": "string", "description": "Base ref (tag, branch, or SHA)."},
                        "to_ref":   {"type": "string", "description": "Target ref (tag, branch, or SHA)."},
                    },
                    "required": [],
                },
                handler=_get_commits,
            ),
            ToolDef(
                name="list_changed_files",
                description=(
                    "Return the file manifest with churn stats (+added -removed lines) and a "
                    "path tag (source, test, lock, vendor, generated, docs, config) for each file. "
                    "Use this to triage which files are worth fetching diffs for."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "from_ref": {"type": "string"},
                        "to_ref":   {"type": "string"},
                    },
                    "required": [],
                },
                handler=_list_changed_files,
            ),
            ToolDef(
                name="get_file_diff",
                description="Return the unified diff for a single file.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path":     {"type": "string", "description": "Repo-relative file path."},
                        "from_ref": {"type": "string"},
                        "to_ref":   {"type": "string"},
                    },
                    "required": ["path"],
                },
                handler=_get_file_diff,
            ),
            ToolDef(
                name="get_diff_for_paths",
                description=(
                    "Return the combined unified diff for a list of files. "
                    "Prefer this over multiple get_file_diff calls."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "paths":    {"type": "array", "items": {"type": "string"}, "description": "List of repo-relative file paths."},
                        "from_ref": {"type": "string"},
                        "to_ref":   {"type": "string"},
                    },
                    "required": ["paths"],
                },
                handler=_get_diff_for_paths,
            ),
            ToolDef(
                name="get_commit_detail",
                description=(
                    "Return the full commit message and the diff introduced by a specific commit SHA. "
                    "Use when a commit message is ambiguous and you need to verify what actually changed."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "sha": {"type": "string", "description": "Full or short commit SHA."},
                    },
                    "required": ["sha"],
                },
                handler=_get_commit_detail,
            ),
        ]
        for d in defs:
            self._tools[d.name] = d

    def all_definitions(self) -> list[ToolDef]:
        return list(self._tools.values())

    def dispatch(self, name: str, args: dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Unknown tool: {name}"
        try:
            return tool.handler(**args)
        except Exception as exc:
            return f"Tool error: {exc}"
