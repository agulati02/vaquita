"""Core data models for Vaquita."""

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
