"""Provider registry for cheat-cli."""

from __future__ import annotations

import os

from .provider import AIProvider, ProviderConfigError


def get_provider(
    name: str | None = None,
    **kwargs,
) -> AIProvider:
    """Get an AI provider instance by name.

    Args:
        name: Provider name ('openai-compatible' or 'ollama').
              Defaults to CHEAT_AI_PROVIDER env var or 'openai-compatible'.
        **kwargs: Provider-specific configuration overrides.

    Returns:
        An AIProvider instance.

    Raises:
        ProviderConfigError: If the provider name is invalid.
    """
    from .providers.ollama import OllamaProvider
    from .providers.openai import OpenAICompatibleProvider

    provider_name = name or os.environ.get("CHEAT_AI_PROVIDER", "openai-compatible")

    providers = {
        "openai-compatible": lambda: OpenAICompatibleProvider(**kwargs),
        "ollama": lambda: OllamaProvider(**kwargs),
    }

    factory = providers.get(provider_name)
    if factory is None:
        available = ", ".join(sorted(providers.keys()))
        raise ProviderConfigError(
            f"Unknown AI provider: '{provider_name}'\n"
            f"Available providers: {available}\n"
            "Set CHEAT_AI_PROVIDER to a valid provider name."
        )

    return factory()


def list_providers() -> list[str]:
    """List available provider names."""
    return ["openai-compatible", "ollama"]