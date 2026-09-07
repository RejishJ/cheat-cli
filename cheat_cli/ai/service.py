"""AI service layer for cheat-cli."""

from __future__ import annotations

from .models import AICommandSuggestion, AIContext
from .provider import AIProvider
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
        """
        if not request or not request.strip():
            raise ValueError("Request must not be empty")

        effective_context = context or AIContext.detect()
        return self.provider.suggest_commands(request.strip(), effective_context)
