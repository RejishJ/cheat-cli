"""Tests for cheat_cli.ai.providers — AI providers (mocked)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from cheat_cli.ai.models import AIContext
from cheat_cli.ai.provider import ProviderConfigError, ProviderRequestError, ProviderResponseError
from cheat_cli.ai.providers.ollama import OllamaProvider
from cheat_cli.ai.providers.openai import OpenAICompatibleProvider


class TestOpenAICompatibleProvider:
    """Tests for OpenAI-compatible provider."""

    def test_name(self) -> None:
        p = OpenAICompatibleProvider(api_key="test-key")
        assert p.name == "openai-compatible"

    def test_requires_api_key(self) -> None:
        p = OpenAICompatibleProvider(api_key="test-key")
        assert p.requires_api_key is True

    def test_missing_api_key_raises(self) -> None:
        p = OpenAICompatibleProvider(api_key="")
        with pytest.raises(ProviderConfigError, match="API key is required"):
            p.suggest_commands("test request")

    def test_custom_config(self) -> None:
        p = OpenAICompatibleProvider(
            api_key="key",
            base_url="https://custom.api.com/v1",
            model="gpt-4",
            timeout=60,
        )
        assert p._api_key == "key"
        assert p._base_url == "https://custom.api.com/v1"
        assert p._model == "gpt-4"
        assert p._timeout == 60

    @patch("cheat_cli.ai.providers.openai.urllib.request.urlopen")
    def test_successful_response(self, mock_urlopen: MagicMock) -> None:
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "suggestions": [
                                    {
                                        "tool": "git",
                                        "command": "git status",
                                        "description": "Show status",
                                        "tags": ["status"],
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        p = OpenAICompatibleProvider(api_key="test-key")
        ctx = AIContext(platform="linux", shell="bash")
        suggestions = p.suggest_commands("show git status", ctx)

        assert len(suggestions) == 1
        assert suggestions[0].command == "git status"

    @patch("cheat_cli.ai.providers.openai.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen: MagicMock) -> None:
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=MagicMock(read=MagicMock(return_value=b"Invalid API key")),
        )

        p = OpenAICompatibleProvider(api_key="bad-key")
        with pytest.raises(ProviderRequestError, match="HTTP 401"):
            p.suggest_commands("test")

    @patch("cheat_cli.ai.providers.openai.urllib.request.urlopen")
    def test_connection_error(self, mock_urlopen: MagicMock) -> None:
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        p = OpenAICompatibleProvider(api_key="test-key")
        with pytest.raises(ProviderRequestError, match="Connection failed"):
            p.suggest_commands("test")

    @patch("cheat_cli.ai.providers.openai.urllib.request.urlopen")
    def test_timeout_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = TimeoutError("timed out")

        p = OpenAICompatibleProvider(api_key="test-key")
        with pytest.raises(ProviderRequestError, match="timed out"):
            p.suggest_commands("test")

    @patch("cheat_cli.ai.providers.openai.urllib.request.urlopen")
    def test_malformed_response(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"invalid": "response"}).encode(
            "utf-8"
        )
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        p = OpenAICompatibleProvider(api_key="test-key")
        with pytest.raises(ProviderResponseError, match="Unexpected response"):
            p.suggest_commands("test")


class TestOllamaProvider:
    """Tests for Ollama provider."""

    def test_name(self) -> None:
        p = OllamaProvider()
        assert p.name == "ollama"

    def test_requires_api_key(self) -> None:
        p = OllamaProvider()
        assert p.requires_api_key is False

    def test_custom_config(self) -> None:
        p = OllamaProvider(
            model="llama3.2",
            base_url="http://custom:11434",
            timeout=120,
        )
        assert p._model == "llama3.2"
        assert p._base_url == "http://custom:11434"
        assert p._timeout == 120

    def test_default_base_url(self) -> None:
        p = OllamaProvider()
        assert p._base_url == "http://localhost:11434"

    @patch("cheat_cli.ai.providers.ollama.urllib.request.urlopen")
    def test_successful_response(self, mock_urlopen: MagicMock) -> None:
        response_data = {
            "message": {
                "content": json.dumps(
                    {
                        "suggestions": [
                            {
                                "tool": "docker",
                                "command": "docker ps",
                                "description": "List containers",
                            }
                        ]
                    }
                )
            }
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        p = OllamaProvider()
        ctx = AIContext(platform="linux", shell="bash")
        suggestions = p.suggest_commands("list containers", ctx)

        assert len(suggestions) == 1
        assert suggestions[0].command == "docker ps"

    @patch("cheat_cli.ai.providers.ollama.urllib.request.urlopen")
    def test_connection_error(self, mock_urlopen: MagicMock) -> None:
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        p = OllamaProvider()
        with pytest.raises(ProviderRequestError, match="Connection failed"):
            p.suggest_commands("test")

    @patch("cheat_cli.ai.providers.ollama.urllib.request.urlopen")
    def test_timeout_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = TimeoutError("timed out")

        p = OllamaProvider()
        with pytest.raises(ProviderRequestError, match="timed out"):
            p.suggest_commands("test")

    @patch("cheat_cli.ai.providers.ollama.urllib.request.urlopen")
    def test_malformed_response(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"unexpected": "format"}).encode(
            "utf-8"
        )
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        p = OllamaProvider()
        with pytest.raises(ProviderResponseError, match="Unexpected response"):
            p.suggest_commands("test")
