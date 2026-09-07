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

    def __post_init__(self) -> None:
        if not self.tool or not self.tool.strip():
            raise ValueError("tool must not be empty")
        if not self.command or not self.command.strip():
            raise ValueError("command must not be empty")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    def matches(self, query: str) -> bool:
        """Case-insensitive partial match across all fields."""
        q = query.lower()
        return (
            q in self.tool.lower()
            or q in self.command.lower()
            or q in self.description.lower()
            or q in self.tags.lower()
        )
