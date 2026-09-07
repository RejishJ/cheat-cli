"""Tests for cheat_cli.core.models."""

from cheat_cli.core.models import CSV_FIELDS, Entry


class TestEntry:
    def test_creation(self):
        e = Entry(tool="git", command="git status", description="Show status", tags="repo")
        assert e.tool == "git"
        assert e.command == "git status"
        assert e.description == "Show status"
        assert e.tags == "repo"

    def test_to_dict(self):
        e = Entry(tool="git", command="git status", description="Show status", tags="repo")
        d = e.to_dict()
        assert d == {
            "tool": "git",
            "command": "git status",
            "description": "Show status",
            "tags": "repo",
        }
        assert list(d.keys()) == CSV_FIELDS

    def test_matches_exact(self):
        e = Entry(tool="git", command="git status", description="Show status", tags="repo")
        assert e.matches("git status")

    def test_matches_case_insensitive(self):
        e = Entry(tool="Git", command="Git Status", description="Show Status", tags="Repo")
        assert e.matches("git status")
        assert e.matches("GIT")

    def test_matches_partial(self):
        e = Entry(tool="git", command="git status", description="Show working tree status", tags="repo state")
        assert e.matches("status")
        assert e.matches("tree")
        assert e.matches("repo")

    def test_matches_in_description(self):
        e = Entry(tool="git", command="git log", description="Show commit history", tags="log")
        assert e.matches("commit")

    def test_matches_in_tags(self):
        e = Entry(tool="git", command="git branch", description="List branches", tags="branch list")
        assert e.matches("list")

    def test_no_match(self):
        e = Entry(tool="git", command="git status", description="Show status", tags="repo")
        assert not e.matches("docker")

    def test_empty_query_matches_all(self):
        e = Entry(tool="git", command="git status", description="Show status", tags="repo")
        assert e.matches("")
