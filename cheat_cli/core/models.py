"""Data models for cheat-cli entries."""

from __future__ import annotations

from dataclasses import asdict, dataclass

CSV_FIELDS: list[str] = ["tool", "command", "description", "tags"]


@dataclass
class Entry:
    """A single cheat-sheet entry."""
    tool: str
    command: str
    description: str
    tags: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    def matches(self, query: str) -> bool:
        """Case-insensitive search across all fields."""
        q = query.lower()
        return any(q in getattr(self, field).lower() for field in CSV_FIELDS)
