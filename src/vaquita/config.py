"""Configuration for a Vaquita run."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .llm_providers import Provider


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


@dataclass
class Config:
    from_ref: str
    to_ref: str
    repo_path: Path = field(default_factory=Path.cwd)
    output_format: OutputFormat = OutputFormat.MARKDOWN
    output_file: Path | None = None
    provider: Provider = Provider.OPENAI
    model: str = "gpt-4o"
