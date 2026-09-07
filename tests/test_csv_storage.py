"""Tests for cheat_cli.core.csv_storage."""

import csv
from pathlib import Path

import pytest

from cheat_cli.core.csv_storage import CSVStorage
from cheat_cli.core.models import CSV_FIELDS, Entry


class TestCSVStorageLoad:
    """Tests for CSVStorage.load()."""

    def test_load_new_format(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({
                "id": "test-id-001",
                "tool": "git",
                "command": "git status",
                "description": "Show status",
                "tags": "repo",
                "platform": "linux",
                "shell": "bash",
                "source": "bundled",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "",
            })
        storage = CSVStorage(csv_path)
        entries = storage.load()
        assert len(entries) == 1
        assert entries[0].id == "test-id-001"
        assert entries[0].platform == "linux"
        assert entries[0].shell == "bash"
        assert entries[0].source == "bundled"
        assert entries[0].created_at == "2026-01-01T00:00:00+00:00"
        assert entries[0].updated_at == ""

    def test_load_legacy_4_column_format(self, tmp_path: Path):
        csv_path = tmp_path / "legacy.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({
                "tool": "git",
                "command": "git status",
                "description": "Show status",
                "tags": "repo",
            })
        storage = CSVStorage(csv_path)
        entries = storage.load()
        assert len(entries) == 1
        assert entries[0].id  # UUID4 generated
        assert len(entries[0].id) == 36
        assert entries[0].tool == "git"
        assert entries[0].source == "user"

    def test_load_legacy_generates_ids(self, tmp_path: Path):
        csv_path = tmp_path / "legacy.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({"tool": "a", "command": "a1", "description": "", "tags": ""})
            writer.writerow({"tool": "b", "command": "b1", "description": "", "tags": ""})
        storage = CSVStorage(csv_path)
        entries = storage.load()
        assert entries[0].id
        assert entries[1].id
        assert entries[0].id != entries[1].id

    def test_load_missing_optional_columns(self, tmp_path: Path):
        csv_path = tmp_path / "partial.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags", "source"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "", "tags": "", "source": "ai"})
        storage = CSVStorage(csv_path)
        entries = storage.load()
        assert entries[0].source == "ai"
        assert entries[0].platform == ""
        assert entries[0].shell == ""

    def test_load_extra_columns_ignored(self, tmp_path: Path):
        csv_path = tmp_path / "extra.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags", "unknown_col"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "", "tags": "", "unknown_col": "value"})
        storage = CSVStorage(csv_path)
        entries = storage.load()
        assert len(entries) == 1
        assert entries[0].tool == "git"

    def test_load_empty_csv(self, tmp_path: Path):
        csv_path = tmp_path / "empty.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
        storage = CSVStorage(csv_path)
        entries = storage.load()
        assert entries == []

    def test_load_nonexistent_raises(self, tmp_path: Path):
        storage = CSVStorage(tmp_path / "nonexistent.csv")
        with pytest.raises(FileNotFoundError):
            storage.load()

    def test_load_malformed_csv(self, tmp_path: Path):
        csv_path = tmp_path / "bad.csv"
        csv_path.write_text("tool,command\ngit,git status\n")
        storage = CSVStorage(csv_path)
        with pytest.raises(ValueError, match="missing required columns"):
            storage.load()

    def test_load_empty_source_defaults_to_user(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerow({
                "id": "", "tool": "git", "command": "git status",
                "description": "", "tags": "", "platform": "", "shell": "",
                "source": "", "created_at": "", "updated_at": "",
            })
        storage = CSVStorage(csv_path)
        entries = storage.load()
        assert entries[0].source == "user"


class TestCSVStorageSave:
    """Tests for CSVStorage.save()."""

    def test_save_writes_new_schema(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        entry = Entry(tool="git", command="git status", description="", tags="",
                      id="test-id", source="bundled",
                      created_at="2026-01-01T00:00:00+00:00")
        storage.save([entry])

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == CSV_FIELDS
            row = next(reader)
            assert row["id"] == "test-id"
            assert row["source"] == "bundled"

    def test_save_atomic_write(self, tmp_path: Path):
        csv_path = tmp_path / "sub" / "dir" / "test.csv"
        storage = CSVStorage(csv_path)
        storage.save([])
        assert csv_path.exists()

    def test_save_empty_list(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        storage.save([])
        entries = storage.load()
        assert entries == []


class TestCSVStorageAdd:
    """Tests for CSVStorage.add()."""

    def test_add_entry(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        storage.save([])
        entry = Entry(tool="git", command="git status", description="", tags="")
        storage.add(entry)
        entries = storage.load()
        assert len(entries) == 1
        assert entries[0].command == "git status"

    def test_add_duplicate_raises(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        entry1 = Entry(tool="git", command="git status", description="", tags="")
        storage.save([entry1])
        entry2 = Entry(tool="git", command="git status", description="other", tags="")
        with pytest.raises(ValueError, match="already exists"):
            storage.add(entry2)

    def test_add_preserves_existing(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        entry1 = Entry(tool="git", command="git status", description="", tags="")
        storage.save([entry1])
        entry2 = Entry(tool="docker", command="docker ps", description="", tags="")
        storage.add(entry2)
        entries = storage.load()
        assert len(entries) == 2


class TestCSVStorageUpdate:
    """Tests for CSVStorage.update()."""

    def test_update_entry(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        original = Entry(tool="git", command="git status", description="Show status", tags="repo")
        storage.save([original])

        updated = Entry(tool="git", command="git status --short", description="Short", tags="repo")
        storage.update(original, updated)

        entries = storage.load()
        assert entries[0].command == "git status --short"

    def test_update_nonexistent_raises(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        original = Entry(tool="x", command="y", description="z", tags="w")
        updated = Entry(tool="a", command="b", description="c", tags="d")
        storage.save([])
        with pytest.raises(ValueError, match="Entry not found"):
            storage.update(original, updated)

    def test_update_conflict_raises(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        e1 = Entry(tool="git", command="git status", description="", tags="")
        e2 = Entry(tool="git", command="git log", description="", tags="")
        storage.save([e1, e2])

        updated = Entry(tool="git", command="git log", description="", tags="")
        with pytest.raises(ValueError, match="already exists"):
            storage.update(e1, updated)

    def test_update_preserves_other_entries(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        e1 = Entry(tool="git", command="git status", description="", tags="")
        e2 = Entry(tool="docker", command="docker ps", description="", tags="")
        storage.save([e1, e2])

        updated = Entry(tool="git", command="git status -v", description="", tags="")
        storage.update(e1, updated)

        entries = storage.load()
        assert len(entries) == 2
        assert entries[0].command == "git status -v"
        assert entries[1].command == "docker ps"


class TestCSVStorageDelete:
    """Tests for CSVStorage.delete()."""

    def test_delete_entry(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        entry = Entry(tool="git", command="git status", description="", tags="")
        storage.save([entry])
        result = storage.delete(entry)
        assert result is True
        assert storage.load() == []

    def test_delete_nonexistent(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        entry = Entry(tool="git", command="git status", description="", tags="")
        storage.save([])
        result = storage.delete(entry)
        assert result is False

    def test_delete_preserves_others(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        e1 = Entry(tool="git", command="git status", description="", tags="")
        e2 = Entry(tool="docker", command="docker ps", description="", tags="")
        storage.save([e1, e2])
        storage.delete(e1)
        entries = storage.load()
        assert len(entries) == 1
        assert entries[0].command == "docker ps"


class TestCSVStorageIDPersistence:
    """Tests for the critical ID persistence behavior."""

    def test_legacy_ids_persist_after_save(self, tmp_path: Path):
        """Load legacy CSV → generate IDs → save → reload → same IDs."""
        csv_path = tmp_path / "test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["tool", "command", "description", "tags"])
            writer.writeheader()
            writer.writerow({"tool": "git", "command": "git status", "description": "", "tags": ""})
            writer.writerow({"tool": "docker", "command": "docker ps", "description": "", "tags": ""})

        storage = CSVStorage(csv_path)
        entries1 = storage.load()
        ids1 = [e.id for e in entries1]

        storage.save(entries1)
        entries2 = storage.load()
        ids2 = [e.id for e in entries2]

        assert ids1 == ids2

    def test_new_format_ids_stable(self, tmp_path: Path):
        """Entries with IDs in CSV remain stable across loads."""
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        e1 = Entry(tool="git", command="git status", description="", tags="",
                    id="stable-id-001", created_at="2026-01-01T00:00:00+00:00")
        e2 = Entry(tool="docker", command="docker ps", description="", tags="",
                    id="stable-id-002", created_at="2026-01-01T00:00:00+00:00")
        storage.save([e1, e2])

        entries = storage.load()
        assert entries[0].id == "stable-id-001"
        assert entries[1].id == "stable-id-002"

    def test_timestamps_preserved(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)
        e = Entry(tool="git", command="git status", description="", tags="",
                  created_at="2026-01-01T00:00:00+00:00",
                  updated_at="2026-06-15T12:00:00+00:00")
        storage.save([e])

        entries = storage.load()
        assert entries[0].created_at == "2026-01-01T00:00:00+00:00"
        assert entries[0].updated_at == "2026-06-15T12:00:00+00:00"


class TestCSVStorageBackendInterface:
    """Tests that CSVStorage satisfies the StorageBackend protocol."""

    def test_load_save_add_update_delete(self, tmp_path: Path):
        csv_path = tmp_path / "test.csv"
        storage = CSVStorage(csv_path)

        # save empty
        storage.save([])
        assert storage.load() == []

        # add
        e1 = Entry(tool="git", command="git status", description="", tags="")
        storage.add(e1)
        entries = storage.load()
        assert len(entries) == 1

        # update
        updated = Entry(tool="git", command="git status -v", description="verbose", tags="")
        storage.update(e1, updated)
        entries = storage.load()
        assert entries[0].command == "git status -v"

        # delete
        assert storage.delete(entries[0]) is True
        assert storage.load() == []
