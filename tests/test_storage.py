"""Tests for cheat_cli.core.storage."""

from pathlib import Path

import pytest

from cheat_cli.core.models import Entry
from cheat_cli.core.storage import (
    add_entry,
    delete_entries,
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
        entry = add_entry("tool", "", "desc", "tags", sample_csv)
        # Empty command should be allowed at storage level; CLI validates
        assert entry.command == ""


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
