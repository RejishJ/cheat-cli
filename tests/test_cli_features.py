"""Tests for cheat_cli.cli — config, doctor, export, import, offline commands."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cheat_cli.cli import main


class TestConfigCommand:
    """Tests for 'cheat config' command."""

    def test_config_get_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("cheat_cli.config.config_path") as mock_path, \
             patch("cheat_cli.config.load_config_file") as mock_load, \
             patch("cheat_cli.config.resolve_config") as mock_resolve:
            mock_path.return_value = Path("/tmp/fake/config.ini")
            mock_load.return_value = MagicMock(
                ai_provider="openai-compatible",
                ai_model="",
                ai_base_url="",
                ai_timeout=30,
                offline=False,
            )
            mock_resolve.return_value = MagicMock(
                ai_provider="openai-compatible",
                ai_model="",
                ai_base_url="",
                ai_timeout=30,
                offline=False,
            )
            result = main(["config", "get"])
            assert result == 0
            captured = capsys.readouterr()
            assert "Current configuration" in captured.out
            assert "provider = openai-compatible" in captured.out

    def test_config_set_valid(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        cfg_file = tmp_path / "config.ini"
        with patch("cheat_cli.config.config_path", return_value=cfg_file):
            result = main(["config", "set", "ai.provider", "ollama"])
            assert result == 0
            captured = capsys.readouterr()
            assert "Set ai.provider = ollama" in captured.out

    def test_config_set_invalid_key(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["config", "set", "invalid.key", "value"])
        assert result == 1
        captured = capsys.readouterr()
        assert "unknown configuration key" in captured.err

    def test_config_set_invalid_provider(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["config", "set", "ai.provider", "invalid"])
        assert result == 1
        captured = capsys.readouterr()
        assert "invalid provider" in captured.err

    def test_config_set_invalid_timeout(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["config", "set", "ai.timeout", "abc"])
        assert result == 1
        captured = capsys.readouterr()
        assert "positive integer" in captured.err

    def test_config_reset(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("cheat_cli.config.reset_config_file") as mock_reset:
            result = main(["config", "reset"])
            assert result == 0
            mock_reset.assert_called_once()
            captured = capsys.readouterr()
            assert "reset to defaults" in captured.out

    def test_config_default_action(self, capsys: pytest.CaptureFixture[str]) -> None:
        """config without subcommand should show config."""
        result = main(["config"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Current configuration" in captured.out


class TestDoctorCommand:
    """Tests for 'cheat doctor' command."""

    def test_doctor_runs(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["doctor"])
        assert result == 0
        captured = capsys.readouterr()
        assert "cheat-cli doctor" in captured.out

    def test_doctor_shows_python_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["doctor"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Python version" in captured.out

    def test_doctor_shows_config(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["doctor"])
        assert result == 0
        captured = capsys.readouterr()
        assert "Configuration" in captured.out


class TestExportCommand:
    """Tests for 'cheat export' command."""

    def test_export_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("cheat_cli.cli.CheatService") as mock_svc:
            mock_svc.return_value.list_entries.return_value = []
            result = main(["export"])
            assert result == 0

    def test_export_to_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        output = tmp_path / "export.csv"
        with patch("cheat_cli.cli.CheatService") as mock_svc:
            mock_entry = MagicMock()
            mock_entry.to_dict.return_value = {
                "tool": "git", "command": "git status",
                "description": "Show status", "tags": "repo"
            }
            mock_svc.return_value.list_entries.return_value = [mock_entry]
            result = main(["export", str(output)])
            assert result == 0
            assert output.exists()
            captured = capsys.readouterr()
            assert "Exported" in captured.out

    def test_export_existing_file_overwrite(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        output = tmp_path / "existing.csv"
        output.write_text("old,data\n")
        with patch("cheat_cli.cli.CheatService") as mock_svc, \
             patch("builtins.input", return_value="yes"):
            mock_svc.return_value.list_entries.return_value = []
            result = main(["export", str(output)])
            assert result == 0

    def test_export_existing_file_cancel(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        output = tmp_path / "existing.csv"
        output.write_text("old,data\n")
        with patch("cheat_cli.cli.CheatService") as mock_svc, \
             patch("builtins.input", return_value="no"):
            mock_svc.return_value.list_entries.return_value = []
            result = main(["export", str(output)])
            assert result == 0
            # File should still have old content
            assert output.read_text() == "old,data\n"


class TestImportCommand:
    """Tests for 'cheat import' command."""

    def test_import_valid_csv(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        input_file = tmp_path / "import.csv"
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git pull", "description": "Pull", "tags": "git"})

        with patch("cheat_cli.core.storage.load_entries", return_value=[]), \
             patch("cheat_cli.core.storage.save_entries") as mock_save:
            result = main(["import", str(input_file)])
            assert result == 0
            mock_save.assert_called_once()
            captured = capsys.readouterr()
            assert "Imported 1" in captured.out

    def test_import_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main(["import", "/nonexistent/file.csv"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_import_skips_duplicates(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        input_file = tmp_path / "import.csv"
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "Status", "tags": ""})

        existing = [MagicMock(command="git status")]
        with patch("cheat_cli.core.storage.load_entries", return_value=existing), \
             patch("cheat_cli.core.storage.save_entries"):
            result = main(["import", str(input_file)])
            assert result == 0
            captured = capsys.readouterr()
            # When all entries are duplicates, we show "All entries already exist"
            assert "already exist" in captured.out.lower() or "skipped" in captured.out.lower()

    def test_import_empty_csv(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        input_file = tmp_path / "empty.csv"
        input_file.write_text("tool,command,description,tags\n")
        with patch("cheat_cli.core.storage.load_entries", return_value=[]):
            result = main(["import", str(input_file)])
            assert result == 0
            captured = capsys.readouterr()
            assert "No valid entries" in captured.out


class TestOfflineFlag:
    """Tests for --offline flag."""

    def test_offline_flag_sets_mode(self) -> None:
        with patch("cheat_cli.config.set_offline_mode") as mock_set:
            main(["--offline", "config", "get"])
            mock_set.assert_called_once_with(True)

    def test_no_offline_flag(self) -> None:
        with patch("cheat_cli.config.set_offline_mode") as mock_set:
            main(["config", "get"])
            mock_set.assert_not_called()
