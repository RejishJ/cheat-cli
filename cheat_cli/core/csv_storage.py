"""CSV storage backend for cheat-cli entries."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from .models import CSV_FIELDS, Entry


class CSVStorage:
    """CSV-backed storage for cheat entries.

    Handles both legacy 4-column CSVs and the new 10-column format.
    IDs are generated for legacy entries and persisted on the next write.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[Entry]:
        """Load all entries from the CSV file.

        Reads old 4-column and new 10-column formats.
        Missing optional columns receive defaults.
        Legacy entries without IDs are assigned UUIDs in memory.

        Raises:
            FileNotFoundError: If the CSV file does not exist.
            ValueError: If the CSV is malformed or missing required columns.
        """
        if not self._path.exists():
            raise FileNotFoundError(f"CSV file not found: {self._path}")

        entries: list[Entry] = []

        with open(self._path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                raise ValueError(f"Empty CSV file: {self._path}")

            required = {"tool", "command", "description", "tags"}
            missing = required - set(reader.fieldnames)
            if missing:
                raise ValueError(
                    f"CSV missing required columns: {', '.join(sorted(missing))}"
                )

            for _row_num, row in enumerate(reader, start=2):
                entries.append(Entry(
                    tool=row.get("tool", "").strip(),
                    command=row.get("command", "").strip(),
                    description=row.get("description", "").strip(),
                    tags=row.get("tags", "").strip(),
                    id=row.get("id", "").strip(),
                    platform=row.get("platform", "").strip(),
                    shell=row.get("shell", "").strip(),
                    source=row.get("source", "user").strip() or "user",
                    created_at=row.get("created_at", "").strip(),
                    updated_at=row.get("updated_at", "").strip(),
                ))

        return entries

    def save(self, entries: list[Entry]) -> None:
        """Save entries to CSV with atomic write (temp file + rename).

        Always writes the full 10-column schema.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._path.parent), suffix=".tmp", prefix="commands_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
                for entry in entries:
                    writer.writerow(entry.to_dict())
            os.replace(tmp_path, str(self._path))
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def add(self, entry: Entry) -> None:
        """Add a single entry to storage.

        Raises:
            ValueError: If a command with the same string already exists.
        """
        entries = self.load()

        for existing in entries:
            if existing.command == entry.command:
                raise ValueError(f"Command already exists: {entry.command}")

        entries.append(entry)
        self.save(entries)

    def update(self, original: Entry, updated: Entry) -> None:
        """Replace original entry with updated entry.

        Matches by comparing all four core fields (tool, command,
        description, tags) of the original.

        Raises:
            ValueError: If the original is not found or the updated command
                conflicts with a different existing entry.
        """
        entries = self.load()

        original_index: int | None = None
        for i, existing in enumerate(entries):
            if (
                existing.tool == original.tool
                and existing.command == original.command
                and existing.description == original.description
                and existing.tags == original.tags
            ):
                original_index = i
                break

        if original_index is None:
            raise ValueError("Entry not found")

        for i, existing in enumerate(entries):
            if i != original_index and existing.command == updated.command:
                raise ValueError(f"Command already exists: {updated.command}")

        entries[original_index] = updated
        self.save(entries)

    def delete(self, entry: Entry) -> bool:
        """Delete an entry by value equality.

        Matches by comparing all four core fields (tool, command,
        description, tags). Removes the first matching entry found.

        Returns:
            True if the entry was found and deleted, False otherwise.
        """
        entries = self.load()
        for i, existing in enumerate(entries):
            if (
                existing.tool == entry.tool
                and existing.command == entry.command
                and existing.description == entry.description
                and existing.tags == entry.tags
            ):
                entries.pop(i)
                self.save(entries)
                return True
        return False
