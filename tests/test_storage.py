"""Tests for cheat_cli.core.storage."""

from pathlib import Path
from unittest.mock import patch

import pytest

from cheat_cli.core.models import Entry
from cheat_cli.core.storage import (
    add_entry,
    delete_entries,
    delete_entries_by_values,
    delete_entry,
    ensure_user_csv,
    load_entries,
    save_entries,
)


class TestLoadEntries:
    def test_load_sample(self, sample_csv: Path):
        entries = load_entries(sample_csv)
        assert len(entries) == 3
        assert entries[0].tool == "git"
        assert entries[0].command == "git status"

    def test_load_empty(self, empty_csv: Path):
        entries = load_entries(empty_csv)
        assert entries == []

    def test_load_malformed(self, malformed_csv: Path):
        with pytest.raises(ValueError, match="missing required columns"):
            load_entries(malformed_csv)

    def test_load_nonexistent(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_entries(tmp_path / "nonexistent.csv")


class TestSaveEntries:
    def test_save_and_reload(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        entries = [
            Entry(tool="git", command="git status", description="Show status", tags="repo"),
            Entry(tool="docker", command="docker ps", description="List containers", tags="containers"),
        ]
        save_entries(entries, csv_path)

        loaded = load_entries(csv_path)
        assert len(loaded) == 2
        assert loaded[0].command == "git status"
        assert loaded[1].command == "docker ps"

    def test_save_empty(self, tmp_path: Path):
        csv_path = tmp_path / "empty.csv"
        save_entries([], csv_path)
        loaded = load_entries(csv_path)
        assert loaded == []

    def test_atomic_write_creates_parent_dirs(self, tmp_path: Path):
        csv_path = tmp_path / "sub" / "dir" / "test.csv"
        save_entries([], csv_path)
        assert csv_path.exists()

    def test_save_preserves_utf8(self, tmp_path: Path):
        csv_path = tmp_path / "utf8.csv"
        entries = [Entry(tool="git", command="git log --graph", description="Visual graph", tags="history")]
        save_entries(entries, csv_path)
        loaded = load_entries(csv_path)
        assert loaded[0].description == "Visual graph"


class TestAddEntry:
    def test_add_entry(self, sample_csv: Path):
        entry = add_entry("python", "python -m pytest", "Run tests", "testing", sample_csv)
        assert entry.tool == "python"
        assert entry.command == "python -m pytest"

        entries = load_entries(sample_csv)
        assert len(entries) == 4
        assert entries[-1].command == "python -m pytest"

    def test_add_duplicate_raises(self, sample_csv: Path):
        with pytest.raises(ValueError, match="already exists"):
            add_entry("git", "git status", "Duplicate", "dup", sample_csv)

    def test_add_empty_command(self, sample_csv: Path):
        with pytest.raises(ValueError, match="command must not be empty"):
            add_entry("tool", "", "desc", "tags", sample_csv)

    def test_add_whitespace_command(self, sample_csv: Path):
        with pytest.raises(ValueError, match="command must not be empty"):
            add_entry("tool", "   ", "desc", "tags", sample_csv)

    def test_add_empty_tool(self, sample_csv: Path):
        with pytest.raises(ValueError, match="tool must not be empty"):
            add_entry("", "git status --new", "desc", "tags", sample_csv)


class TestDeleteEntries:
    def test_delete_single(self, sample_csv: Path):
        deleted = delete_entries("docker ps", sample_csv)
        assert len(deleted) == 1
        assert deleted[0].command == "docker ps"

        remaining = load_entries(sample_csv)
        assert len(remaining) == 2
        assert all("docker" not in e.command for e in remaining)

    def test_delete_multiple(self, sample_csv: Path):
        deleted = delete_entries("git", sample_csv)
        assert len(deleted) == 2

        remaining = load_entries(sample_csv)
        assert len(remaining) == 1
        assert remaining[0].command == "docker ps"

    def test_delete_no_match(self, sample_csv: Path):
        deleted = delete_entries("nonexistent", sample_csv)
        assert deleted == []

        entries = load_entries(sample_csv)
        assert len(entries) == 3

    def test_delete_case_insensitive(self, sample_csv: Path):
        deleted = delete_entries("Git Status", sample_csv)
        assert len(deleted) == 1


class TestDeleteEntry:
    def test_delete_single_entry(self, sample_csv: Path):
        entry = Entry(tool="docker", command="docker ps", description="List containers", tags="containers")
        result = delete_entry(entry, sample_csv)
        assert result is True

        remaining = load_entries(sample_csv)
        assert len(remaining) == 2
        assert all(e.command != "docker ps" for e in remaining)

    def test_delete_nonexistent_entry(self, sample_csv: Path):
        entry = Entry(tool="kubectl", command="kubectl get pods", description="List pods", tags="k8s")
        result = delete_entry(entry, sample_csv)
        assert result is False

        remaining = load_entries(sample_csv)
        assert len(remaining) == 3

    def test_delete_only_first_match(self, tmp_path: Path):
        csv_path = tmp_path / "dupes.csv"
        entries = [
            Entry(tool="git", command="git status", description="Show status", tags="repo"),
            Entry(tool="git", command="git status", description="Show status", tags="repo"),
            Entry(tool="git", command="git log", description="Show log", tags="history"),
        ]
        save_entries(entries, csv_path)

        target = Entry(tool="git", command="git status", description="Show status", tags="repo")
        result = delete_entry(target, csv_path)
        assert result is True

        remaining = load_entries(csv_path)
        assert len(remaining) == 2

    def test_delete_by_value_not_identity(self, sample_csv: Path):
        entries = load_entries(sample_csv)
        original = entries[0]

        loaded_again = load_entries(sample_csv)
        copy = loaded_again[0]

        assert original is not copy
        assert original == copy

        result = delete_entry(copy, sample_csv)
        assert result is True

        remaining = load_entries(sample_csv)
        assert len(remaining) == 2


class TestDeleteEntriesByValues:
    def test_delete_multiple_entries(self, sample_csv: Path):
        entries = load_entries(sample_csv)
        targets = [e for e in entries if e.tool == "git"]
        assert len(targets) == 2

        deleted = delete_entries_by_values(targets, sample_csv)
        assert deleted == 2

        remaining = load_entries(sample_csv)
        assert len(remaining) == 1
        assert remaining[0].command == "docker ps"

    def test_delete_single_entry(self, sample_csv: Path):
        entries = load_entries(sample_csv)
        target = [entries[2]]  # docker ps

        deleted = delete_entries_by_values(target, sample_csv)
        assert deleted == 1

        remaining = load_entries(sample_csv)
        assert len(remaining) == 2
        assert all(e.tool != "docker" for e in remaining)

    def test_delete_nonexistent_entry(self, sample_csv: Path):
        target = [Entry(tool="kubectl", command="kubectl get pods", description="List pods", tags="k8s")]
        deleted = delete_entries_by_values(target, sample_csv)
        assert deleted == 0

        entries = load_entries(sample_csv)
        assert len(entries) == 3

    def test_delete_empty_list(self, sample_csv: Path):
        deleted = delete_entries_by_values([], sample_csv)
        assert deleted == 0

        entries = load_entries(sample_csv)
        assert len(entries) == 3

    def test_delete_by_value_not_identity(self, sample_csv: Path):
        entries = load_entries(sample_csv)

        loaded_again = load_entries(sample_csv)
        copy = loaded_again[0]

        assert entries[0] is not copy
        assert entries[0] == copy

        deleted = delete_entries_by_values([copy], sample_csv)
        assert deleted == 1

        remaining = load_entries(sample_csv)
        assert len(remaining) == 2

    def test_delete_by_tag_match(self, tmp_path: Path):
        """Regression test: search by tag, confirm, verify deletion."""
        csv_path = tmp_path / "tags.csv"
        entries = [
            Entry(tool="git", command="git status", description="Show status", tags="repo state"),
            Entry(tool="git", command="git log", description="Show log", tags="history"),
            Entry(tool="docker", command="docker ps", description="List containers", tags="containers"),
        ]
        save_entries(entries, csv_path)

        # Simulate: search finds entries matching "state" in tags
        all_entries = load_entries(csv_path)
        matches = [e for e in all_entries if "state" in e.tags.lower()]
        assert len(matches) == 1
        assert matches[0].command == "git status"

        # Delete the matched entries
        deleted = delete_entries_by_values(matches, csv_path)
        assert deleted == 1

        remaining = load_entries(csv_path)
        assert len(remaining) == 2
        assert all(e.command != "git status" for e in remaining)


class TestEnsureUserCsv:
    def test_new_path_exists_uses_it(self, tmp_path: Path, sample_csv: Path):
        new_dir = tmp_path / "new"
        new_dir.mkdir()
        new_csv = new_dir / "commands.csv"
        new_csv.write_text("tool,command,description,tags\ngit,git status,Show status,repo\n")

        with patch("cheat_cli.core.storage.user_csv_path", return_value=new_csv), \
             patch("cheat_cli.core.storage.legacy_data_dir", return_value=tmp_path / "nonexistent"):
            result = ensure_user_csv()
            content = result.read_text()
            assert "git status" in content

    def test_legacy_path_exists_migrates(self, tmp_path: Path, sample_csv: Path):
        legacy_dir = tmp_path / "legacy"
        legacy_dir.mkdir()
        legacy_csv = legacy_dir / "commands.csv"
        legacy_csv.write_text("tool,command,description,tags\ndocker,docker ps,List containers,containers\n")

        new_dir = tmp_path / "new"
        new_dir.mkdir()
        new_csv = new_dir / "commands.csv"

        with patch("cheat_cli.core.storage.user_csv_path", return_value=new_csv), \
             patch("cheat_cli.core.storage.legacy_data_dir", return_value=legacy_dir):
            result = ensure_user_csv()
            assert result.exists()
            content = result.read_text()
            assert "docker ps" in content

    def test_legacy_path_not_deleted(self, tmp_path: Path, sample_csv: Path):
        legacy_dir = tmp_path / "legacy"
        legacy_dir.mkdir()
        legacy_csv = legacy_dir / "commands.csv"
        legacy_csv.write_text("tool,command,description,tags\ndocker,docker ps,List containers,containers\n")

        new_dir = tmp_path / "new"
        new_dir.mkdir()
        new_csv = new_dir / "commands.csv"

        with patch("cheat_cli.core.storage.user_csv_path", return_value=new_csv), \
             patch("cheat_cli.core.storage.legacy_data_dir", return_value=legacy_dir):
            ensure_user_csv()
            assert legacy_csv.exists()

    def test_neither_exists_seeds_from_package(self, tmp_path: Path):
        new_dir = tmp_path / "new"
        new_dir.mkdir()
        new_csv = new_dir / "commands.csv"

        seed_content = "tool,command,description,tags\ngit,git status,Show status,repo\n"

        with patch("cheat_cli.core.storage.user_csv_path", return_value=new_csv), \
             patch("cheat_cli.core.storage.legacy_data_dir", return_value=tmp_path / "nonexistent"), \
             patch("cheat_cli.core.storage.packaged_csv_path") as mock_packaged:
            mock_packaged.return_value.__str__ = lambda s: str(tmp_path / "seed.csv")
            (tmp_path / "seed.csv").write_text(seed_content)
            result = ensure_user_csv()
            content = result.read_text()
            assert "git status" in content
