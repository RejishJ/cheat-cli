"""AI provider abstraction for cheat-cli."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import AICommandSuggestion, AIContext


class ProviderError(Exception):
    """Base exception for AI provider errors."""


class ProviderConfigError(ProviderError):
    """Raised when provider configuration is missing or invalid."""


class ProviderRequestError(ProviderError):
    """Raised when a provider request fails."""


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an invalid response."""


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI command suggestion providers."""

    @property
    def name(self) -> str:
        """Return the provider name."""
        ...

    @property
    def requires_api_key(self) -> bool:
        """Return True if this provider requires an API key."""
        ...

    @property
    def is_local(self) -> bool:
        """Return True if this provider is local (no external network)."""
        ...

    def suggest_commands(
        self,
        request: str,
        context: AIContext | None = None,
    ) -> list[AICommandSuggestion]:
        """Request command suggestions from the AI provider.

        Args:
            request: The user's request describing what they want to do.
            context: Optional environment context.

        Returns:
            List of command suggestions.

        Raises:
            ProviderConfigError: If configuration is missing.
            ProviderRequestError: If the request fails.
            ProviderResponseError: If the response is invalid.
        """
        ...
