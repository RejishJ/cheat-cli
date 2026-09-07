"""Tests for offline mode integration with AI providers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cheat_cli.ai.provider import ProviderConfigError


class TestOfflineMode:
    """Tests for offline mode behavior."""

    def test_cloud_provider_rejected_offline(self) -> None:
        from cheat_cli.ai.providers.openai import OpenAICompatibleProvider
        from cheat_cli.config import set_offline_mode

        set_offline_mode(True)
        try:
            provider = OpenAICompatibleProvider(api_key="test-key")
            with pytest.raises(ProviderConfigError, match="Offline mode"):
                provider.suggest_commands("test")
        finally:
            set_offline_mode(False)

    def test_ollama_allowed_offline(self) -> None:
        """Ollama is a local provider, should work in offline mode."""
        from cheat_cli.ai.providers.ollama import OllamaProvider
        from cheat_cli.config import set_offline_mode

        set_offline_mode(True)
        try:
            provider = OllamaProvider()
            assert provider.is_local is True
            # We can't actually call suggest_commands without Ollama running,
            # but we can verify the provider doesn't reject offline mode
            # by checking it doesn't raise ProviderConfigError for offline
        finally:
            set_offline_mode(False)

    def test_ai_service_offline_rejects_cloud(self) -> None:
        from cheat_cli.ai.service import AIService
        from cheat_cli.config import set_offline_mode

        set_offline_mode(True)
        try:
            mock_provider = MagicMock()
            mock_provider.name = "openai-compatible"
            mock_provider.is_local = False
            service = AIService(provider=mock_provider)
            with pytest.raises(ProviderConfigError, match="Offline mode"):
                service.suggest("test")
        finally:
            set_offline_mode(False)

    def test_ai_service_offline_allows_local(self) -> None:
        from cheat_cli.ai.service import AIService
        from cheat_cli.config import set_offline_mode

        set_offline_mode(True)
        try:
            mock_provider = MagicMock()
            mock_provider.name = "ollama"
            mock_provider.is_local = True
            mock_provider.suggest_commands.return_value = []
            service = AIService(provider=mock_provider)
            # Should not raise
            result = service.suggest("test")
            assert result == []
        finally:
            set_offline_mode(False)

    def test_provider_is_local_property(self) -> None:
        from cheat_cli.ai.providers.ollama import OllamaProvider
        from cheat_cli.ai.providers.openai import OpenAICompatibleProvider

        assert OpenAICompatibleProvider(api_key="key").is_local is False
        assert OllamaProvider().is_local is True
