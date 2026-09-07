"""AI service layer for cheat-cli."""

from __future__ import annotations

from .models import AICommandSuggestion, AIContext
from .provider import AIProvider, ProviderConfigError
from .registry import get_provider


class AIService:
    """Service for AI command suggestions."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> AIProvider:
        """Get the current provider, lazy-loading if needed."""
        if self._provider is None:
            self._provider = get_provider()
        return self._provider

    def suggest(
        self,
        request: str,
        context: AIContext | None = None,
    ) -> list[AICommandSuggestion]:
        """Request command suggestions.

        Args:
            request: The user's request.
            context: Optional environment context.

        Returns:
            List of command suggestions.

        Raises:
            ProviderError: If the request fails.
            ProviderConfigError: If offline mode prevents the request.
        """
        from ..config import is_offline

        if not request or not request.strip():
            raise ValueError("Request must not be empty")

        # Check offline mode before attempting any provider call
        if is_offline() and not self.provider.is_local:
            raise ProviderConfigError(
                f"Offline mode is active.\n"
                f"The '{self.provider.name}' provider requires network access.\n"
                f"Use a local provider (ollama) or disable offline mode."
            )

        effective_context = context or AIContext.detect()
        return self.provider.suggest_commands(request.strip(), effective_context)
