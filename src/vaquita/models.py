"""Core data models for Vaquita."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ChangeType(str, Enum):
    BREAKING = "breaking"
    FEATURE = "feature"
    FIX = "fix"
    CHORE = "chore"
    DOCS = "docs"
    UNKNOWN = "unknown"


@dataclass
class Commit:
    sha: str
    message: str
    author: str
    email: str = ""
    timestamp: str = ""
    pr_number: int | None = None
    pr_title: str | None = None


@dataclass
class ReleaseSection:
    change_type: ChangeType
    entries: list[str] = field(default_factory=list)


@dataclass
class ReleaseNotes:
    from_ref: str
    to_ref: str
    sections: list[ReleaseSection] = field(default_factory=list)
    commits: list[Commit] = field(default_factory=list)


@dataclass
class ToolCall:
    name: str
    args: dict
    call_id: str


@dataclass
class Response:
    content: str | None = None
    tool_call: ToolCall | None = None


@dataclass
class Message:
    role: str
    content: str | None = None
    tool_call: ToolCall | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None


@dataclass
class TurnRecord:
    turn: int
    type: str
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result_preview: str | None = None
    model_output_preview: str | None = None


@dataclass
class AgentTrace:
    turns: list[TurnRecord] = field(default_factory=list)
    total_tool_calls: int = 0
    final_output: str = ""
