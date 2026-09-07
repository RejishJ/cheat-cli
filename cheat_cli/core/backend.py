"""Storage backend protocol for cheat-cli."""

from __future__ import annotations

from typing import Protocol

from .models import Entry


class StorageBackend(Protocol):
    """Protocol for entry storage backends."""

    def load(self) -> list[Entry]:
        """Load all entries from storage."""
        ...

    def save(self, entries: list[Entry]) -> None:
        """Save all entries to storage."""
        ...

    def add(self, entry: Entry) -> None:
        """Add a single entry to storage.

        Raises:
            ValueError: If a command with the same string already exists.
        """
        ...

    def update(self, original: Entry, updated: Entry) -> None:
        """Replace original entry with updated entry.

        Raises:
            ValueError: If the original is not found or the updated command
                conflicts with a different existing entry.
        """
        ...

    def delete(self, entry: Entry) -> bool:
        """Delete an entry by value equality.

        Returns:
            True if the entry was found and deleted, False otherwise.
        """
        ...
