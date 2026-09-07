"""Tests for cheat_cli.ai.service — AI service layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cheat_cli.ai.models import AICommandSuggestion, AIContext
from cheat_cli.ai.provider import ProviderError
from cheat_cli.ai.service import AIService


class TestAIService:
    """Tests for AIService."""

    def test_suggest_empty_request(self) -> None:
        service = AIService()
        with pytest.raises(ValueError, match="Request must not be empty"):
            service.suggest("")

    def test_suggest_whitespace_request(self) -> None:
        service = AIService()
        with pytest.raises(ValueError, match="Request must not be empty"):
            service.suggest("   ")

    def test_suggest_with_mock_provider(self) -> None:
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_provider.suggest_commands.return_value = [
            AICommandSuggestion(
                command="git status",
                description="Show status",
                tool="git",
            )
        ]

        service = AIService(provider=mock_provider)
        suggestions = service.suggest("show git status")

        assert len(suggestions) == 1
        assert suggestions[0].command == "git status"
        mock_provider.suggest_commands.assert_called_once()

    def test_suggest_with_custom_context(self) -> None:
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_provider.suggest_commands.return_value = []

        service = AIService(provider=mock_provider)
        ctx = AIContext(platform="linux", shell="bash")
        service.suggest("test", context=ctx)

        call_args = mock_provider.suggest_commands.call_args
        assert call_args[0][1] == ctx

    def test_suggest_provider_error(self) -> None:
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_provider.suggest_commands.side_effect = ProviderError("Provider failed")

        service = AIService(provider=mock_provider)
        with pytest.raises(ProviderError, match="Provider failed"):
            service.suggest("test")

    def test_lazy_provider_loading(self) -> None:
        service = AIService()
        with patch("cheat_cli.ai.service.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_get.return_value = mock_provider

            # Access provider to trigger lazy loading
            _ = service.provider
            mock_get.assert_called_once()
