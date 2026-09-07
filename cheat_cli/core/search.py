"""Search functionality for cheat-cli entries."""

from __future__ import annotations

from .models import Entry


def search_entries(entries: list[Entry], query: str) -> list[Entry]:
    """Search entries across all fields (case-insensitive).

    Args:
        entries: List of Entry objects to search.
        query: Search string.

    Returns:
        List of matching Entry objects.
    """
    if not query:
        return list(entries)
    return [e for e in entries if e.matches(query)]
