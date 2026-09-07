"""CSV storage layer for cheat-cli entries.

Provides backward-compatible module-level functions that delegate to CSVStorage.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .csv_storage import CSVStorage
from .models import Entry
from .paths import legacy_data_dir, packaged_csv_path, user_csv_path


def ensure_user_csv() -> Path:
    """Ensure the user's CSV file exists, migrating or seeding as needed.

    Handles three cases:
      A) New path already exists -> use it (no overwrite).
      B) New path missing, legacy path exists -> copy legacy data to new location.
      C) Neither exists -> initialize from bundled seed CSV.

    Returns:
        Path to the user's CSV file.
    """
    path = user_csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        return path

    legacy_csv = legacy_data_dir() / "commands.csv"
    if legacy_csv.exists():
        shutil.copy2(str(legacy_csv), str(path))
        return path

    shutil.copy(str(packaged_csv_path()), str(path))
    return path


def load_entries(csv_path: Path | None = None) -> list[Entry]:
    """Load all entries from the CSV file.

    Args:
        csv_path: Path to CSV file. If None, uses the user's default path.

    Returns:
        List of Entry objects.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV is malformed or missing required columns.
    """
    path = csv_path or ensure_user_csv()
    return CSVStorage(path).load()


def save_entries(entries: list[Entry], csv_path: Path | None = None) -> None:
    """Save entries to CSV with atomic write (temp file + rename).

    Args:
        entries: List of Entry objects to save.
        csv_path: Path to CSV file. If None, uses the user's default path.
    """
    path = csv_path or user_csv_path()
    CSVStorage(path).save(entries)


def add_entry(
    tool: str,
    command: str,
    description: str,
    tags: str,
    csv_path: Path | None = None,
) -> Entry:
    """Add a new entry to the CSV file.

    Returns:
        The newly created Entry.

    Raises:
        ValueError: If a command with the same string already exists.
    """
    path = csv_path or ensure_user_csv()
    entry = Entry(tool=tool, command=command, description=description, tags=tags)
    CSVStorage(path).add(entry)
    return entry


def delete_entry(
    entry: Entry,
    csv_path: Path | None = None,
) -> bool:
    """Delete a single entry by value equality.

    Returns:
        True if the entry was found and deleted, False otherwise.
    """
    path = csv_path or ensure_user_csv()
    return CSVStorage(path).delete(entry)


def delete_entries_by_values(
    targets: list[Entry],
    csv_path: Path | None = None,
) -> int:
    """Delete specific entries by value equality.

    Returns:
        Number of entries deleted.
    """
    if not targets:
        return 0

    path = csv_path or ensure_user_csv()
    storage = CSVStorage(path)
    entries = storage.load()

    target_set = {(t.tool, t.command, t.description, t.tags) for t in targets}
    remaining = [
        e for e in entries
        if (e.tool, e.command, e.description, e.tags) not in target_set
    ]
    deleted_count = len(entries) - len(remaining)
    if deleted_count > 0:
        storage.save(remaining)
    return deleted_count


def update_entry(
    original: Entry,
    tool: str,
    command: str,
    description: str,
    tags: str,
    csv_path: Path | None = None,
) -> Entry:
    """Update an existing entry by value equality.

    Returns:
        The newly created Entry that replaced the original.

    Raises:
        ValueError: If the original is not found, or if the new command
            conflicts with a different existing entry.
    """
    path = csv_path or ensure_user_csv()
    updated = Entry(tool=tool, command=command, description=description, tags=tags)
    CSVStorage(path).update(original, updated)
    return updated


def delete_entries(
    query: str,
    csv_path: Path | None = None,
) -> list[Entry]:
    """Delete entries matching a query.

    Returns:
        List of deleted entries (empty if no matches).
    """
    path = csv_path or ensure_user_csv()
    storage = CSVStorage(path)
    entries = storage.load()
    matching = [e for e in entries if query.lower() in e.command.lower()]

    if not matching:
        return []

    remaining = [e for e in entries if e not in matching]
    storage.save(remaining)
    return matching
