"""CSV storage layer for cheat-cli entries."""

from __future__ import annotations

import csv
import os
import shutil
import tempfile
from pathlib import Path

from .models import CSV_FIELDS, Entry
from .paths import legacy_data_dir, packaged_csv_path, user_csv_path


def ensure_user_csv() -> Path:
    """Ensure the user's CSV file exists, migrating or seeding as needed.

    Handles three cases:
      A) New path already exists → use it (no overwrite).
      B) New path missing, legacy path exists → copy legacy data to new location.
      C) Neither exists → initialize from bundled seed CSV.

    Returns:
        Path to the user's CSV file.
    """
    path = user_csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Case A: new path already exists
    if path.exists():
        return path

    # Case B: legacy path exists → migrate (copy, don't delete original)
    legacy_csv = legacy_data_dir() / "commands.csv"
    if legacy_csv.exists():
        shutil.copy2(str(legacy_csv), str(path))
        return path

    # Case C: neither exists → seed from package
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
    entries: list[Entry] = []

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"Empty CSV file: {path}")

        missing = set(CSV_FIELDS) - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"CSV missing required columns: {', '.join(sorted(missing))}"
            )

        for row_num, row in enumerate(reader, start=2):
            try:
                entries.append(Entry(
                    tool=row.get("tool", "").strip(),
                    command=row.get("command", "").strip(),
                    description=row.get("description", "").strip(),
                    tags=row.get("tags", "").strip(),
                ))
            except KeyError as e:
                raise ValueError(f"CSV row {row_num} missing field: {e}")

    return entries


def save_entries(entries: list[Entry], csv_path: Path | None = None) -> None:
    """Save entries to CSV with atomic write (temp file + rename).

    Args:
        entries: List of Entry objects to save.
        csv_path: Path to CSV file. If None, uses the user's default path.
    """
    path = csv_path or user_csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory, then atomically rename
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), suffix=".tmp", prefix="commands_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_dict())
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def add_entry(
    tool: str,
    command: str,
    description: str,
    tags: str,
    csv_path: Path | None = None,
) -> Entry:
    """Add a new entry to the CSV file.

    Args:
        tool: Tool name.
        command: The command string.
        description: Human-readable description.
        tags: Space-separated tags.
        csv_path: Path to CSV file. If None, uses the user's default path.

    Returns:
        The newly created Entry.

    Raises:
        ValueError: If a command with the same string already exists.
    """
    entries = load_entries(csv_path)

    for existing in entries:
        if existing.command == command:
            raise ValueError(f"Command already exists: {command}")

    entry = Entry(tool=tool, command=command, description=description, tags=tags)
    entries.append(entry)
    save_entries(entries, csv_path)
    return entry


def delete_entry(
    entry: Entry,
    csv_path: Path | None = None,
) -> bool:
    """Delete a single entry by value equality.

    Matches by comparing all four fields (tool, command, description, tags).
    Removes the first matching entry found.

    Args:
        entry: The entry to delete (matched by value, not identity).
        csv_path: Path to CSV file. If None, uses the user's default path.

    Returns:
        True if the entry was found and deleted, False otherwise.
    """
    entries = load_entries(csv_path)
    for i, existing in enumerate(entries):
        if (
            existing.tool == entry.tool
            and existing.command == entry.command
            and existing.description == entry.description
            and existing.tags == entry.tags
        ):
            entries.pop(i)
            save_entries(entries, csv_path)
            return True
    return False


def delete_entries_by_values(
    targets: list[Entry],
    csv_path: Path | None = None,
) -> int:
    """Delete specific entries by value equality.

    Each target is matched by comparing all four fields (tool, command,
    description, tags). Removes the first matching entry found for each target.

    Args:
        targets: List of entries to delete (matched by value, not identity).
        csv_path: Path to CSV file. If None, uses the user's default path.

    Returns:
        Number of entries deleted.
    """
    if not targets:
        return 0

    entries = load_entries(csv_path)
    target_set = {(t.tool, t.command, t.description, t.tags) for t in targets}
    remaining = [
        e for e in entries
        if (e.tool, e.command, e.description, e.tags) not in target_set
    ]
    deleted_count = len(entries) - len(remaining)
    if deleted_count > 0:
        save_entries(remaining, csv_path)
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

    Finds the first entry matching all four fields of `original` and replaces
    it with a new entry built from the provided values.  If the new command
    already exists in a *different* entry, raises ValueError.

    Args:
        original: The entry to replace (matched by value, not identity).
        tool: New tool name.
        command: New command string.
        description: New description.
        tags: New tags string.
        csv_path: Path to CSV file. If None, uses the user's default path.

    Returns:
        The newly created Entry that replaced the original.

    Raises:
        ValueError: If the original is not found, or if the new command
            conflicts with a different existing entry.
    """
    entries = load_entries(csv_path)

    # Locate the original entry
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

    # Check for command conflict with a *different* entry
    for i, existing in enumerate(entries):
        if i != original_index and existing.command == command:
            raise ValueError(f"Command already exists: {command}")

    updated = Entry(tool=tool, command=command, description=description, tags=tags)
    entries[original_index] = updated
    save_entries(entries, csv_path)
    return updated


def delete_entries(
    query: str,
    csv_path: Path | None = None,
) -> list[Entry]:
    """Delete entries matching a query.

    Args:
        query: Search query to match against commands.
        csv_path: Path to CSV file. If None, uses the user's default path.

    Returns:
        List of deleted entries (empty if no matches).
    """
    entries = load_entries(csv_path)
    matching = [e for e in entries if query.lower() in e.command.lower()]

    if not matching:
        return []

    remaining = [e for e in entries if e not in matching]
    save_entries(remaining, csv_path)
    return matching
