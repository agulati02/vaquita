from __future__ import annotations

import json
from dataclasses import dataclass, field

from .config import Config
from .llm import chat
from .models import (
    AgentTrace,
    ChangeType,
    Message,
    ReleaseNotes,
    ReleaseSection,
    TurnRecord,
    ToolCall,
)
from .tool_registry import ToolRegistry

_INITIAL_PROMPT = (
    "Generate release notes for the changes between `{from_ref}` and `{to_ref}`. "
    "Use the available tools to inspect the repository. Produce the final JSON when ready."
)


def _infer_change_type(title: str) -> ChangeType:
    t = title.lower()
    if any(w in t for w in ("break", "incompatible", "removal")):
        return ChangeType.BREAKING
    if any(w in t for w in ("feat", "add", "new")):
        return ChangeType.FEATURE
    if any(w in t for w in ("fix", "bug", "patch", "correct")):
        return ChangeType.FIX
    if any(w in t for w in ("doc", "readme", "changelog")):
        return ChangeType.DOCS
    if any(w in t for w in ("chore", "refactor", "ci", "build", "dep", "maintenance")):
        return ChangeType.CHORE
    return ChangeType.UNKNOWN


def _parse_release_notes(from_ref: str, to_ref: str, raw: str) -> ReleaseNotes:
    parsed = json.loads(raw)
    sections = [
        ReleaseSection(
            change_type=_infer_change_type(s.get("title", "")),
            entries=s.get("changes", []),
        )
        for s in parsed.get("sections", [])
    ]
    return ReleaseNotes(from_ref=from_ref, to_ref=to_ref, sections=sections)


@dataclass
class AgentOrchestrator:
    config: Config
    registry: ToolRegistry = field(init=False)

    def __post_init__(self) -> None:
        self.registry = ToolRegistry(
            self.config.repo_path,
            self.config.from_ref,
            self.config.to_ref,
        )

    def run(self) -> tuple[ReleaseNotes, AgentTrace]:
        trace = AgentTrace()
        tools = self.registry.all_definitions()
        messages: list[Message] = [
            Message(
                role="user",
                content=_INITIAL_PROMPT.format(
                    from_ref=self.config.from_ref,
                    to_ref=self.config.to_ref,
                ),
            )
        ]

        for turn in range(self.config.max_turns):
            response = chat(messages, self.config.provider, self.config.model, tools)

            if response.tool_call:
                tc: ToolCall = response.tool_call
                result = self.registry.dispatch(tc.name, tc.args)

                trace.turns.append(TurnRecord(
                    turn=turn,
                    type="tool_call",
                    tool_name=tc.name,
                    tool_args=tc.args,
                    tool_result_preview=result[:200],
                ))
                trace.total_tool_calls += 1

                messages.append(Message(role="assistant", tool_call=tc))
                messages.append(Message(
                    role="tool",
                    content=result,
                    tool_call_id=tc.call_id,
                    tool_name=tc.name,
                ))
                continue

            if response.content:
                raw = response.content.strip()
                trace.turns.append(TurnRecord(
                    turn=turn,
                    type="final",
                    model_output_preview=raw[:200],
                ))
                trace.final_output = raw
                return _parse_release_notes(self.config.from_ref, self.config.to_ref, raw), trace

        raise RuntimeError(f"Agent did not produce output within {self.config.max_turns} turns.")


def generate_notes(config: Config) -> tuple[ReleaseNotes, AgentTrace]:
    return AgentOrchestrator(config=config).run()
