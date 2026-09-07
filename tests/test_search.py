"""Tests for cheat_cli.core.search."""

from cheat_cli.core.models import Entry
from cheat_cli.core.search import search_entries


class TestSearchEntries:
    def test_search_by_tool(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "git")
        assert len(results) == 2
        assert all(e.tool == "git" for e in results)

    def test_search_by_command(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "docker ps")
        assert len(results) == 1
        assert results[0].command == "docker ps"

    def test_search_by_description(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "containers")
        assert len(results) == 1
        assert results[0].command == "docker ps"

    def test_search_by_tags(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "repo")
        assert len(results) == 1
        assert results[0].command == "git status"

    def test_search_case_insensitive(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "DOCKER")
        assert len(results) == 1

    def test_search_partial_match(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "stat")
        assert len(results) == 1
        assert results[0].command == "git status"

    def test_search_no_match(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "kubectl")
        assert results == []

    def test_search_empty_query_returns_all(self, sample_entries: list[Entry]):
        results = search_entries(sample_entries, "")
        assert len(results) == 3

    def test_search_empty_list(self):
        results = search_entries([], "git")
        assert results == []
