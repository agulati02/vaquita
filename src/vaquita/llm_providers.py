from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .models import Message, Response
    from .tool_registry import ToolDef


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"


LLMClient = Callable[["list[Message]", "list[ToolDef] | None"], "Response"]


# ---------------------------------------------------------------------------
# Message serialisers
# ---------------------------------------------------------------------------

def _openai_messages(messages: list[Message]) -> list[dict]:
    out = []
    for m in messages:
        if m.role == "tool":
            out.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content or ""})
        elif m.role == "assistant" and m.tool_call:
            out.append({
                "role": "assistant",
                "tool_calls": [{
                    "id": m.tool_call.call_id,
                    "type": "function",
                    "function": {"name": m.tool_call.name, "arguments": __import__("json").dumps(m.tool_call.args)},
                }],
            })
        else:
            out.append({"role": m.role, "content": m.content or ""})
    return out


def _anthropic_messages(messages: list[Message]) -> tuple[str, list[dict]]:
    system = ""
    out = []
    for m in messages:
        if m.role == "system":
            system = m.content or ""
            continue
        if m.role == "assistant" and m.tool_call:
            out.append({
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "id": m.tool_call.call_id,
                    "name": m.tool_call.name,
                    "input": m.tool_call.args,
                }],
            })
        elif m.role == "tool":
            out.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": m.tool_call_id,
                    "content": m.content or "",
                }],
            })
        else:
            out.append({"role": m.role, "content": m.content or ""})
    return system, out


# ---------------------------------------------------------------------------
# Tool definition serialisers
# ---------------------------------------------------------------------------

def _openai_tools(tools: list[ToolDef]) -> list[dict]:
    return [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}} for t in tools]


def _anthropic_tools(tools: list[ToolDef]) -> list[dict]:
    return [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools]


# ---------------------------------------------------------------------------
# Provider factories
# ---------------------------------------------------------------------------

def _make_openai_client(model: str, system_prompt: str) -> LLMClient:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError("openai package required. Install with: uv add openai") from exc

    import json
    from .models import Response, ToolCall

    _client = OpenAI()

    def call(messages: list[Message], tools: list[ToolDef] | None = None) -> Response:
        msgs = _openai_messages(messages)
        kwargs: dict = {"model": model, "messages": msgs}
        if tools:
            kwargs["tools"] = _openai_tools(tools)
        resp = _client.chat.completions.create(**kwargs)
        choice = resp.choices[0].message
        if choice.tool_calls:
            tc = choice.tool_calls[0]
            return Response(tool_call=ToolCall(
                name=tc.function.name,
                args=json.loads(tc.function.arguments),
                call_id=tc.id,
            ))
        return Response(content=choice.content or "")

    return call


def _make_anthropic_client(model: str, system_prompt: str) -> LLMClient:
    try:
        import anthropic
    except ImportError as exc:
        raise ImportError("anthropic package required. Install with: uv add anthropic") from exc

    from .models import Response, ToolCall

    _client = anthropic.Anthropic()

    def call(messages: list[Message], tools: list[ToolDef] | None = None) -> Response:
        system, msgs = _anthropic_messages(messages)
        kwargs: dict = {"model": model, "max_tokens": 4096, "messages": msgs}
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = _anthropic_tools(tools)
        resp = _client.messages.create(**kwargs)
        for block in resp.content:
            if block.type == "tool_use":
                return Response(tool_call=ToolCall(name=block.name, args=block.input, call_id=block.id))
        text = next((b.text for b in resp.content if hasattr(b, "text")), "")
        return Response(content=text)

    return call


def _make_mistral_client(model: str, system_prompt: str) -> LLMClient:
    try:
        from mistralai import Mistral
    except ImportError as exc:
        raise ImportError("mistralai package required. Install with: uv add mistralai") from exc

    import json
    from .models import Response, ToolCall

    _client = Mistral()

    def call(messages: list[Message], tools: list[ToolDef] | None = None) -> Response:
        msgs = _openai_messages(messages)
        kwargs: dict = {"model": model, "messages": msgs}
        if tools:
            kwargs["tools"] = _openai_tools(tools)
        resp = _client.chat.complete(**kwargs)
        choice = resp.choices[0].message
        if choice.tool_calls:
            tc = choice.tool_calls[0]
            return Response(tool_call=ToolCall(
                name=tc.function.name,
                args=json.loads(tc.function.arguments),
                call_id=tc.id,
            ))
        return Response(content=choice.content or "")

    return call


# ---------------------------------------------------------------------------
# Registry and public factory
# ---------------------------------------------------------------------------

_REGISTRY: dict[Provider, Callable[[str, str], LLMClient]] = {
    Provider.OPENAI: _make_openai_client,
    Provider.ANTHROPIC: _make_anthropic_client,
    Provider.MISTRAL: _make_mistral_client,
}


def get_client(provider: Provider | str, model: str, system_prompt: str = "") -> LLMClient:
    try:
        resolved = Provider(provider)
    except ValueError:
        supported = ", ".join(p.value for p in Provider)
        raise ValueError(f"Unknown provider {provider!r}. Supported: {supported}")
    return _REGISTRY[resolved](model, system_prompt)
