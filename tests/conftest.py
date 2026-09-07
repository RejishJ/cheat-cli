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
    """Create a temporary CSV file with sample data."""
    csv_path = tmp_path / "commands.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow({
            "tool": "git",
            "command": "git status",
            "description": "Show working tree status",
            "tags": "repo state",
        })
        writer.writerow({
            "tool": "git",
            "command": "git log --oneline",
            "description": "Compact log",
            "tags": "history",
        })
        writer.writerow({
            "tool": "docker",
            "command": "docker ps",
            "description": "List containers",
            "tags": "containers",
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
    """Create a temporary CSV file with missing columns."""
    csv_path = tmp_path / "malformed.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        f.write("tool,command\n")
        f.write("git,git status\n")
    return csv_path
