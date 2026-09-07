"""Shared test fixtures for cheat-cli tests."""

import csv
from pathlib import Path

import pytest

from cheat_cli.core.models import CSV_FIELDS, Entry


@pytest.fixture
def sample_entries() -> list[Entry]:
    """A small set of entries for testing."""
    return [
        Entry(tool="git", command="git status", description="Show working tree status", tags="repo state"),
        Entry(tool="git", command="git log --oneline", description="Compact log", tags="history"),
        Entry(tool="docker", command="docker ps", description="List containers", tags="containers"),
    ]


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a temporary CSV file with sample data in the new 10-column format."""
    csv_path = tmp_path / "commands.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow({
            "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01",
            "tool": "git",
            "command": "git status",
            "description": "Show working tree status",
            "tags": "repo state",
            "platform": "",
            "shell": "",
            "source": "bundled",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "",
        })
        writer.writerow({
            "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa02",
            "tool": "git",
            "command": "git log --oneline",
            "description": "Compact log",
            "tags": "history",
            "platform": "",
            "shell": "",
            "source": "bundled",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "",
        })
        writer.writerow({
            "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa03",
            "tool": "docker",
            "command": "docker ps",
            "description": "List containers",
            "tags": "containers",
            "platform": "",
            "shell": "",
            "source": "bundled",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "",
        })
    return csv_path


@pytest.fixture
def empty_csv(tmp_path: Path) -> Path:
    """Create a temporary CSV file with headers only."""
    csv_path = tmp_path / "empty.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
    return csv_path


@pytest.fixture
def malformed_csv(tmp_path: Path) -> Path:
    """Create a temporary CSV file with missing required columns."""
    csv_path = tmp_path / "malformed.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        f.write("tool,command\n")
        f.write("git,git status\n")
    return csv_path
