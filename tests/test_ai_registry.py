"""Tests for cheat_cli.ai.registry — Provider registry."""

from __future__ import annotations

import pytest

from cheat_cli.ai.provider import ProviderConfigError
from cheat_cli.ai.providers.ollama import OllamaProvider
from cheat_cli.ai.providers.openai import OpenAICompatibleProvider
from cheat_cli.ai.registry import get_provider, list_providers


class TestListProviders:
    """Tests for list_providers."""

    def test_returns_list(self) -> None:
        providers = list_providers()
        assert isinstance(providers, list)
        assert "openai-compatible" in providers
        assert "ollama" in providers


class TestGetProvider:
    """Tests for get_provider."""

    def test_default_provider(self) -> None:
        p = get_provider()
        assert isinstance(p, OpenAICompatibleProvider)

    def test_openai_compatible(self) -> None:
        p = get_provider("openai-compatible")
        assert isinstance(p, OpenAICompatibleProvider)

    def test_ollama(self) -> None:
        p = get_provider("ollama")
        assert isinstance(p, OllamaProvider)

    def test_invalid_provider(self) -> None:
        with pytest.raises(ProviderConfigError, match="Unknown AI provider"):
            get_provider("invalid-provider")

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CHEAT_AI_PROVIDER", "ollama")
        p = get_provider()
        assert isinstance(p, OllamaProvider)

    def test_name_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CHEAT_AI_PROVIDER", "ollama")
        p = get_provider("openai-compatible")
        assert isinstance(p, OpenAICompatibleProvider)

    def test_kwargs_passed_to_provider(self) -> None:
        p = get_provider("openai-compatible", api_key="test-key")
        assert isinstance(p, OpenAICompatibleProvider)
        assert p._api_key == "test-key"

    def test_ollama_kwargs(self) -> None:
        p = get_provider("ollama", model="custom-model")
        assert isinstance(p, OllamaProvider)
        assert p._model == "custom-model"
