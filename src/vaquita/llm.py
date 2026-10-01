from __future__ import annotations

from pathlib import Path

from .llm_providers import Provider, get_client
from .models import Message, Response
from .tool_registry import ToolDef

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


def chat(
    messages: list[Message],
    provider: Provider | str,
    model: str,
    tools: list[ToolDef] | None = None,
) -> Response:
    system_prompt = _load_prompt("system.prompt")
    full_messages = [Message(role="system", content=system_prompt)] + messages
    client = get_client(provider=provider, model=model)
    return client(full_messages, tools)
