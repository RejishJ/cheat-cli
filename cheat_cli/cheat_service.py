"""Application service for cheat-cli.

Provides a clean API for CLI and future TUI to use
without depending on storage/search internals directly.
"""

from __future__ import annotations

from pathlib import Path

from .core.models import Entry
from .core.search import search_entries
from .core.storage import add_entry as storage_add_entry
from .core.storage import delete_entries_by_values as storage_delete_entries_by_values
from .core.storage import delete_entry as storage_delete_entry
from .core.storage import load_entries


class CheatService:
    """Application service coordinating cheat-cli operations."""

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_path = csv_path

    def list_entries(self) -> list[Entry]:
        """Load all entries from storage."""
        return load_entries(self._csv_path)

    def search_filtered(self, entries: list[Entry], query: str) -> list[Entry]:
        """Filter a pre-loaded list of entries by query across all fields."""
        return search_entries(entries, query)

    def search_all(self, query: str) -> list[Entry]:
        """Load all entries and filter by query across all fields."""
        return search_entries(load_entries(self._csv_path), query)

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
        return storage_add_entry(tool, command, description, tags, self._csv_path)

    def delete_entry(self, entry: Entry) -> bool:
        """Delete a single entry by value equality.

        Returns:
            True if deleted, False if not found.
        """
        return storage_delete_entry(entry, self._csv_path)

    def delete_entries_by_values(self, entries: list[Entry]) -> int:
        """Delete specific entries by value equality.

        Returns:
            Number of entries deleted.
        """
        return storage_delete_entries_by_values(entries, self._csv_path)
