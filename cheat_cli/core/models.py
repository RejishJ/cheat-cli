"""Data models for cheat-cli entries."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

CSV_FIELDS: list[str] = [
    "id", "tool", "command", "description", "tags",
    "platform", "shell", "source", "created_at", "updated_at",
]


def _new_id() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Entry:
    """A single cheat-sheet entry."""
    tool: str
    command: str
    description: str
    tags: str
    id: str = ""
    platform: str = ""
    shell: str = ""
    source: str = "user"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.tool or not self.tool.strip():
            raise ValueError("tool must not be empty")
        if not self.command or not self.command.strip():
            raise ValueError("command must not be empty")
        if not self.id:
            self.id = _new_id()
        if not self.created_at:
            self.created_at = _now_iso()

    def to_dict(self) -> dict[str, str]:
        d = asdict(self)
        return {k: d[k] for k in CSV_FIELDS}

    def matches(self, query: str) -> bool:
        """Case-insensitive partial match across all fields."""
        q = query.lower()
        return (
            q in self.tool.lower()
            or q in self.command.lower()
            or q in self.description.lower()
            or q in self.tags.lower()
            or q in self.platform.lower()
            or q in self.shell.lower()
            or q in self.source.lower()
        )
