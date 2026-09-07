"""Tests for cheat_cli.cheat_service."""

from pathlib import Path

import pytest

from cheat_cli.cheat_service import CheatService
from cheat_cli.core.models import Entry


@pytest.fixture
def service(tmp_path: Path) -> CheatService:
    """Create a CheatService with a temporary CSV file."""
    csv_path = tmp_path / "commands.csv"
    csv_path.write_text(
        "tool,command,description,tags\n"
        "git,git status,Show working tree status,repo state\n"
        "git,git log --oneline,Compact log,history\n"
        "docker,docker ps,List containers,containers\n"
    )
    return CheatService(csv_path=csv_path)


class TestListEntries:
    def test_loads_entries(self, service: CheatService):
        entries = service.list_entries()
        assert len(entries) == 3
        assert entries[0].tool == "git"
        assert entries[0].command == "git status"

    def test_returns_list_type(self, service: CheatService):
        entries = service.list_entries()
        assert isinstance(entries, list)
        assert all(isinstance(e, Entry) for e in entries)


class TestSearch:
    def test_search_filters_by_tool(self, service: CheatService):
        entries = service.list_entries()
        results = service.search(entries, "git")
        assert len(results) == 2
        assert all(e.tool == "git" for e in results)

    def test_search_filters_by_command(self, service: CheatService):
        entries = service.list_entries()
        results = service.search(entries, "docker ps")
        assert len(results) == 1
        assert results[0].command == "docker ps"

    def test_search_filters_by_description(self, service: CheatService):
        entries = service.list_entries()
        results = service.search(entries, "containers")
        assert len(results) == 1

    def test_search_filters_by_tags(self, service: CheatService):
        entries = service.list_entries()
        results = service.search(entries, "repo")
        assert len(results) == 1

    def test_search_case_insensitive(self, service: CheatService):
        entries = service.list_entries()
        results = service.search(entries, "DOCKER")
        assert len(results) == 1

    def test_search_no_match(self, service: CheatService):
        entries = service.list_entries()
        results = service.search(entries, "kubectl")
        assert results == []

    def test_search_empty_query_returns_all(self, service: CheatService):
        entries = service.list_entries()
        results = service.search(entries, "")
        assert len(results) == 3


class TestAddEntry:
    def test_add_valid_entry(self, service: CheatService):
        entry = service.add_entry("python", "python -m pytest", "Run tests", "testing")
        assert entry.tool == "python"
        assert entry.command == "python -m pytest"

        entries = service.list_entries()
        assert len(entries) == 4
        assert entries[-1].command == "python -m pytest"

    def test_add_duplicate_raises(self, service: CheatService):
        with pytest.raises(ValueError, match="already exists"):
            service.add_entry("git", "git status", "Duplicate", "dup")

    def test_add_empty_command_raises(self, service: CheatService):
        with pytest.raises(ValueError, match="command must not be empty"):
            service.add_entry("tool", "", "desc", "tags")

    def test_add_empty_tool_raises(self, service: CheatService):
        with pytest.raises(ValueError, match="tool must not be empty"):
            service.add_entry("", "git status --new", "desc", "tags")


class TestDeleteEntry:
    def test_delete_existing_entry(self, service: CheatService):
        entry = Entry(tool="docker", command="docker ps", description="List containers", tags="containers")
        result = service.delete_entry(entry)
        assert result is True

        entries = service.list_entries()
        assert len(entries) == 2
        assert all(e.command != "docker ps" for e in entries)

    def test_delete_nonexistent_entry(self, service: CheatService):
        entry = Entry(tool="kubectl", command="kubectl get pods", description="List pods", tags="k8s")
        result = service.delete_entry(entry)
        assert result is False

        entries = service.list_entries()
        assert len(entries) == 3

    def test_delete_by_value(self, service: CheatService):
        entries = service.list_entries()
        original = entries[0]

        loaded_again = service.list_entries()
        copy = loaded_again[0]

        assert original is not copy

        result = service.delete_entry(copy)
        assert result is True

        remaining = service.list_entries()
        assert len(remaining) == 2


class TestSearchAll:
    def test_search_all_filters(self, service: CheatService):
        results = service.search_all("git")
        assert len(results) == 2
        assert all(e.tool == "git" for e in results)

    def test_search_all_no_match(self, service: CheatService):
        results = service.search_all("kubectl")
        assert results == []

    def test_search_all_empty_query_returns_all(self, service: CheatService):
        results = service.search_all("")
        assert len(results) == 3

    def test_search_all_by_tag(self, service: CheatService):
        results = service.search_all("repo")
        assert len(results) == 1
        assert results[0].command == "git status"

    def test_search_all_case_insensitive(self, service: CheatService):
        results = service.search_all("DOCKER")
        assert len(results) == 1


class TestDeleteEntriesByValues:
    def test_delete_matched_entries(self, service: CheatService):
        entries = service.list_entries()
        matches = service.search(entries, "git")
        assert len(matches) == 2

        deleted = service.delete_entries_by_values(matches)
        assert deleted == 2

        remaining = service.list_entries()
        assert len(remaining) == 1
        assert remaining[0].command == "docker ps"

    def test_delete_by_tag_search(self, service: CheatService):
        """Regression: search by tag, delete those exact entries."""
        entries = service.list_entries()
        matches = service.search(entries, "repo")
        assert len(matches) == 1
        assert matches[0].command == "git status"

        deleted = service.delete_entries_by_values(matches)
        assert deleted == 1

        remaining = service.list_entries()
        assert len(remaining) == 2
        assert all(e.command != "git status" for e in remaining)

    def test_delete_no_matches(self, service: CheatService):
        deleted = service.delete_entries_by_values([])
        assert deleted == 0

        entries = service.list_entries()
        assert len(entries) == 3

    def test_delete_nonexistent_entry(self, service: CheatService):
        fake = Entry(tool="kubectl", command="kubectl get pods", description="List pods", tags="k8s")
        deleted = service.delete_entries_by_values([fake])
        assert deleted == 0

        entries = service.list_entries()
        assert len(entries) == 3
