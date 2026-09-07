"""Tests for cheat_cli.cli — AI CLI command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cheat_cli.cli import main


class TestAICLICommand:
    """Tests for 'cheat ai' command."""

    def test_ai_missing_request(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["ai"])
        assert exc_info.value.code == 2

    def test_ai_help(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["ai", "--help"])
        assert exc_info.value.code == 0

    def test_ai_provider_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("cheat_cli.ai.registry.get_provider") as mock_get:
            from cheat_cli.ai.provider import ProviderConfigError

            mock_get.side_effect = ProviderConfigError("Missing config")
            result = main(["ai", "test request"])
            assert result == 1
            captured = capsys.readouterr()
            assert "Missing config" in captured.err

    def test_ai_successful_suggestions(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("cheat_cli.ai.registry.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "mock-provider"
            mock_provider.suggest_commands.return_value = [
                MagicMock(
                    command="git status",
                    description="Show working tree status",
                    tool="git",
                    tags=["status"],
                )
            ]
            mock_get.return_value = mock_provider

            result = main(["ai", "show git status"])
            assert result == 0
            captured = capsys.readouterr()
            assert "git status" in captured.out
            assert "mock-provider" in captured.out

    def test_ai_no_suggestions(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("cheat_cli.ai.registry.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "mock-provider"
            mock_provider.suggest_commands.return_value = []
            mock_get.return_value = mock_provider

            result = main(["ai", "test"])
            assert result == 0
            captured = capsys.readouterr()
            assert "No suggestions" in captured.out

    def test_ai_provider_request_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("cheat_cli.ai.registry.get_provider") as mock_get:
            from cheat_cli.ai.provider import ProviderRequestError

            mock_provider = MagicMock()
            mock_provider.suggest_commands.side_effect = ProviderRequestError(
                "Connection failed"
            )
            mock_get.return_value = mock_provider

            result = main(["ai", "test"])
            assert result == 1
            captured = capsys.readouterr()
            assert "Connection failed" in captured.err

    def test_ai_with_provider_flag(self) -> None:
        with patch("cheat_cli.ai.registry.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "ollama"
            mock_provider.suggest_commands.return_value = []
            mock_get.return_value = mock_provider

            main(["ai", "--provider", "ollama", "test"])
            # Verify provider was called with name="ollama"
            call_kwargs = mock_get.call_args
            assert call_kwargs[1]["name"] == "ollama"

    def test_ai_with_model_flag(self) -> None:
        with patch("cheat_cli.ai.registry.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "mock"
            mock_provider.suggest_commands.return_value = []
            mock_get.return_value = mock_provider

            main(["ai", "--model", "gpt-4", "test"])
            # Verify model was passed to get_provider
            call_kwargs = mock_get.call_args
            assert call_kwargs[1]["model"] == "gpt-4"

    def test_ai_no_context_flag(self) -> None:
        with patch("cheat_cli.ai.registry.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.name = "mock"
            mock_provider.suggest_commands.return_value = []
            mock_get.return_value = mock_provider

            main(["ai", "--no-context", "test"])
            # Context should be None when --no-context is passed
            call_args = mock_provider.suggest_commands.call_args
            assert call_args[0][1] is None

    def test_search_remains_non_interactive(self) -> None:
        """Ensure cheat search doesn't launch TUI."""
        with patch("cheat_cli.cli._try_launch_tui") as mock_tui:
            mock_tui.return_value = False
            with patch("cheat_cli.cli.CheatService") as mock_service:
                mock_service.return_value.list_entries.return_value = []
                mock_service.return_value.search_filtered.return_value = []
                result = main(["search", "test"])
                assert result == 0
                mock_tui.assert_not_called()
