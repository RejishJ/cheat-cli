"""Tests for cheat_cli.cli import/export with the new CSV format."""

import csv
from pathlib import Path
from unittest.mock import MagicMock, patch

from cheat_cli.cli import main
from cheat_cli.core.models import CSV_FIELDS, Entry
from cheat_cli.core.storage import load_entries, save_entries


class TestExportNewFormat:
    """Tests for export with the new 10-column format."""

    def test_export_writes_all_columns(self, tmp_path: Path, capsys):
        csv_path = tmp_path / "commands.csv"
        save_entries([
            Entry(tool="git", command="git status", description="Show status", tags="repo",
                  id="test-id-001", source="bundled",
                  created_at="2026-01-01T00:00:00+00:00"),
        ], csv_path)

        with patch("cheat_cli.cli.CheatService") as mock_svc:
            mock_svc.return_value.list_entries.return_value = load_entries(csv_path)
            output = tmp_path / "export.csv"
            result = main(["export", str(output)])
            assert result == 0

        with open(output, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == CSV_FIELDS
            row = next(reader)
            assert row["id"] == "test-id-001"
            assert row["source"] == "bundled"

    def test_export_to_stdout_new_format(self, capsys):
        with patch("cheat_cli.cli.CheatService") as mock_svc:
            entry = Entry(tool="git", command="git status", description="", tags="",
                          id="stdout-id", source="ai")
            mock_svc.return_value.list_entries.return_value = [entry]
            result = main(["export"])
            assert result == 0
        captured = capsys.readouterr()
        assert "stdout-id" in captured.out


class TestImportNewFormat:
    """Tests for import with the new CSV format."""

    def test_import_old_4_column_csv(self, tmp_path: Path, capsys):
        input_file = tmp_path / "old.csv"
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git pull", "description": "Pull", "tags": "git"})

        with patch("cheat_cli.core.storage.load_entries", return_value=[]), \
             patch("cheat_cli.core.storage.save_entries") as mock_save:
            result = main(["import", str(input_file)])
            assert result == 0
            mock_save.assert_called_once()
            saved_entries = mock_save.call_args[0][0]
            assert len(saved_entries) == 1
            assert saved_entries[0].id  # UUID generated
            assert saved_entries[0].source == "user"

    def test_import_new_10_column_csv(self, tmp_path: Path, capsys):
        input_file = tmp_path / "new.csv"
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({
                "id": "imported-id-001",
                "tool": "git",
                "command": "git pull",
                "description": "Pull",
                "tags": "git",
                "platform": "linux",
                "shell": "bash",
                "source": "bundled",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "",
            })

        with patch("cheat_cli.core.storage.load_entries", return_value=[]), \
             patch("cheat_cli.core.storage.save_entries") as mock_save:
            result = main(["import", str(input_file)])
            assert result == 0
            saved_entries = mock_save.call_args[0][0]
            assert saved_entries[0].id == "imported-id-001"
            assert saved_entries[0].source == "bundled"

    def test_import_missing_id_generates(self, tmp_path: Path, capsys):
        input_file = tmp_path / "noid.csv"
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git pull", "description": "", "tags": ""})

        with patch("cheat_cli.core.storage.load_entries", return_value=[]), \
             patch("cheat_cli.core.storage.save_entries") as mock_save:
            result = main(["import", str(input_file)])
            assert result == 0
            saved_entries = mock_save.call_args[0][0]
            assert saved_entries[0].id  # Generated
            assert len(saved_entries[0].id) == 36

    def test_import_empty_source_defaults_to_user(self, tmp_path: Path, capsys):
        input_file = tmp_path / "test.csv"
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({
                "id": "", "tool": "git", "command": "git pull",
                "description": "", "tags": "", "platform": "", "shell": "",
                "source": "", "created_at": "", "updated_at": "",
            })

        with patch("cheat_cli.core.storage.load_entries", return_value=[]), \
             patch("cheat_cli.core.storage.save_entries") as mock_save:
            result = main(["import", str(input_file)])
            assert result == 0
            saved_entries = mock_save.call_args[0][0]
            assert saved_entries[0].source == "user"

    def test_import_skips_duplicates(self, tmp_path: Path, capsys):
        input_file = tmp_path / "dup.csv"
        with open(input_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "", "tags": ""})

        existing = [MagicMock(command="git status")]
        with patch("cheat_cli.core.storage.load_entries", return_value=existing), \
             patch("cheat_cli.core.storage.save_entries"):
            result = main(["import", str(input_file)])
            assert result == 0
            captured = capsys.readouterr()
            assert "already exist" in captured.out.lower() or "skipped" in captured.out.lower()

    def test_import_file_not_found(self, capsys):
        result = main(["import", "/nonexistent/file.csv"])
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err
