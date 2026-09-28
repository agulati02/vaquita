"""Functional factory pattern for LLM clients.

Each provider is a factory function that accepts a model name and returns a
callable with a uniform signature:

    client(prompt: str) -> str

New providers are registered by adding an entry to _REGISTRY
"""

from __future__ import annotations

from enum import Enum
from typing import Callable


# ---------------------------------------------------------------------------
# Public API types
# ---------------------------------------------------------------------------

LLMClient = Callable[[str], str]


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"


# ---------------------------------------------------------------------------
# Provider factories
# ---------------------------------------------------------------------------

def _make_openai_client(model: str) -> LLMClient:
    """Return an OpenAI chat completion client for the given model."""
    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "openai package is required for the OpenAI provider. "
            "Install it with: uv add openai"
        ) from exc

    _client = OpenAI()

    def call(prompt: str) -> str:
        response = _client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    return call


def _make_anthropic_client(model: str) -> LLMClient:
    """Return an Anthropic messages client for the given model."""
    try:
        import anthropic  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "anthropic package is required for the Anthropic provider. "
            "Install it with: uv add anthropic"
        ) from exc

    _client = anthropic.Anthropic()

    def call(prompt: str) -> str:
        message = _client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    return call


def _make_mistral_client(model: str) -> LLMClient:
    """Return a Mistral chat client for the given model."""
    try:
        from mistralai import Mistral  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "mistralai package is required for the Mistral provider. "
            "Install it with: uv add mistralai"
        ) from exc

    _client = Mistral()

    def call(prompt: str) -> str:
        response = _client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    return call


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[Provider, Callable[[str], LLMClient]] = {
    Provider.OPENAI: _make_openai_client,
    Provider.ANTHROPIC: _make_anthropic_client,
    Provider.MISTRAL: _make_mistral_client,
}


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def get_client(provider: Provider | str, model: str) -> LLMClient:
    """Return an LLMClient for the given provider and model.

    Args:
        provider: A Provider enum value or its string equivalent
                  ("openai", "anthropic", "mistral").
        model:    The model identifier to pass to the provider's API
                  (e.g. "gpt-4o", "claude-opus-4-5", "mistral-large-latest").

    Returns:
        A callable ``(prompt: str) -> str`` backed by the requested provider.

    Raises:
        ValueError: If the provider is not registered.
        ImportError: If the provider's SDK is not installed.
    """
    try:
        resolved = Provider(provider)
    except ValueError:
        supported = ", ".join(p.value for p in Provider)
        raise ValueError(
            f"Unknown provider {provider!r}. Supported providers: {supported}"
        )

    factory = _REGISTRY[resolved]
    return factory(model)
