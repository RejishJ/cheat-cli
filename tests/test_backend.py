"""Tests for cheat_cli.core.backend and CheatService backend injection."""

from pathlib import Path

from cheat_cli.cheat_service import CheatService
from cheat_cli.core.backend import StorageBackend
from cheat_cli.core.csv_storage import CSVStorage


class TestStorageBackendProtocol:
    """Verify CSVStorage satisfies the StorageBackend protocol."""

    def test_csv_storage_is_backend(self):
        from typing import runtime_checkable
        assert runtime_checkable(StorageBackend)
        csv_storage = CSVStorage(Path("/tmp/test.csv"))
        assert hasattr(csv_storage, "load")
        assert hasattr(csv_storage, "save")
        assert hasattr(csv_storage, "add")
        assert hasattr(csv_storage, "update")
        assert hasattr(csv_storage, "delete")


class TestCheatServiceBackendInjection:
    """Test CheatService with injected backend."""

    def test_default_backend_uses_csv(self, tmp_path: Path):
        csv_path = tmp_path / "commands.csv"
        csv_path.write_text(
            "id,tool,command,description,tags,platform,shell,source,created_at,updated_at\n"
            ",git,git status,Show status,repo,,,,user,,\n"
        )
        service = CheatService(csv_path=csv_path)
        entries = service.list_entries()
        assert len(entries) == 1
        assert entries[0].command == "git status"

    def test_injected_backend(self, tmp_path: Path):
        csv_path = tmp_path / "commands.csv"
        csv_path.write_text(
            "id,tool,command,description,tags,platform,shell,source,created_at,updated_at\n"
            ",git,git status,Show status,repo,,,,user,,\n"
        )
        backend = CSVStorage(csv_path)
        service = CheatService(backend=backend)
        entries = service.list_entries()
        assert len(entries) == 1

    def test_service_add_via_backend(self, tmp_path: Path):
        csv_path = tmp_path / "commands.csv"
        csv_path.write_text(
            "id,tool,command,description,tags,platform,shell,source,created_at,updated_at\n"
        )
        service = CheatService(csv_path=csv_path)
        entry = service.add_entry("git", "git status", "Show status", "repo")
        assert entry.command == "git status"
        entries = service.list_entries()
        assert len(entries) == 1

    def test_service_delete_via_backend(self, tmp_path: Path):
        csv_path = tmp_path / "commands.csv"
        csv_path.write_text(
            "id,tool,command,description,tags,platform,shell,source,created_at,updated_at\n"
            ",git,git status,Show status,repo,,,,user,,\n"
        )
        service = CheatService(csv_path=csv_path)
        entry = service.list_entries()[0]
        result = service.delete_entry(entry)
        assert result is True
        assert service.list_entries() == []

    def test_service_update_via_backend(self, tmp_path: Path):
        csv_path = tmp_path / "commands.csv"
        csv_path.write_text(
            "id,tool,command,description,tags,platform,shell,source,created_at,updated_at\n"
            ",git,git status,Show status,repo,,,,user,,\n"
        )
        service = CheatService(csv_path=csv_path)
        original = service.list_entries()[0]
        updated = service.update_entry(original, "git", "git status -v", "Verbose", "repo")
        assert updated.command == "git status -v"
        entries = service.list_entries()
        assert entries[0].command == "git status -v"
