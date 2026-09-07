"""Application service for cheat-cli.

Provides a clean API for CLI and future TUI to use
without depending on storage/search internals directly.
"""

from __future__ import annotations

from pathlib import Path

from .core.backend import StorageBackend
from .core.csv_storage import CSVStorage
from .core.models import Entry
from .core.search import search_entries
from .core.storage import ensure_user_csv


class CheatService:
    """Application service coordinating cheat-cli operations."""

    def __init__(
        self,
        csv_path: Path | None = None,
        backend: StorageBackend | None = None,
    ) -> None:
        if backend is not None:
            self._backend = backend
        elif csv_path is not None:
            self._backend = CSVStorage(csv_path)
        else:
            self._backend = CSVStorage(ensure_user_csv())

    def list_entries(self) -> list[Entry]:
        """Load all entries from storage."""
        return self._backend.load()

    def search_filtered(self, entries: list[Entry], query: str) -> list[Entry]:
        """Filter a pre-loaded list of entries by query across all fields."""
        return search_entries(entries, query)

    def search_all(self, query: str) -> list[Entry]:
        """Load all entries and filter by query across all fields."""
        return search_entries(self._backend.load(), query)

    def add_entry(
        self,
        tool: str,
        command: str,
        description: str,
        tags: str,
    ) -> Entry:
        """Add a new entry.

        Raises:
            ValueError: If the entry is invalid or a duplicate command exists.
        """
        entry = Entry(tool=tool, command=command, description=description, tags=tags)
        self._backend.add(entry)
        return entry

    def delete_entry(self, entry: Entry) -> bool:
        """Delete a single entry by value equality.

        Returns:
            True if deleted, False if not found.
        """
        return self._backend.delete(entry)

    def update_entry(
        self,
        original: Entry,
        tool: str,
        command: str,
        description: str,
        tags: str,
    ) -> Entry:
        """Update an existing entry by value equality.

        Raises:
            ValueError: If the entry is not found or command conflicts.
        """
        updated = Entry(tool=tool, command=command, description=description, tags=tags)
        self._backend.update(original, updated)
        return updated

    def delete_entries_by_values(self, entries: list[Entry]) -> int:
        """Delete specific entries by value equality.

        Returns:
            Number of entries deleted.
        """
        if not entries:
            return 0
        deleted = 0
        for entry in entries:
            if self._backend.delete(entry):
                deleted += 1
        return deleted
