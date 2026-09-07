"""Tests for cheat_cli.ai — AI domain models."""

from __future__ import annotations

import json

import pytest

from cheat_cli.ai.models import (
    AICommandSuggestion,
    AIContext,
    build_system_prompt,
    parse_suggestions,
)


class TestAICommandSuggestion:
    """Tests for AICommandSuggestion model."""

    def test_valid_suggestion(self) -> None:
        s = AICommandSuggestion(
            command="git status",
            description="Show working tree status",
            tool="git",
            tags=["status", "repo"],
            platform="linux",
            shell="bash",
        )
        assert s.command == "git status"
        assert s.description == "Show working tree status"
        assert s.tool == "git"
        assert s.tags == ["status", "repo"]
        assert s.platform == "linux"
        assert s.shell == "bash"

    def test_empty_command_raises(self) -> None:
        with pytest.raises(ValueError, match="command must not be empty"):
            AICommandSuggestion(
                command="",
                description="desc",
                tool="tool",
            )

    def test_whitespace_command_raises(self) -> None:
        with pytest.raises(ValueError, match="command must not be empty"):
            AICommandSuggestion(
                command="   ",
                description="desc",
                tool="tool",
            )

    def test_empty_description_raises(self) -> None:
        with pytest.raises(ValueError, match="description must not be empty"):
            AICommandSuggestion(
                command="cmd",
                description="",
                tool="tool",
            )

    def test_empty_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="tool must not be empty"):
            AICommandSuggestion(
                command="cmd",
                description="desc",
                tool="",
            )

    def test_tags_from_string(self) -> None:
        s = AICommandSuggestion(
            command="cmd",
            description="desc",
            tool="tool",
            tags="git, status, repo",
        )
        assert s.tags == ["git", "status", "repo"]

    def test_tags_empty_string(self) -> None:
        s = AICommandSuggestion(
            command="cmd",
            description="desc",
            tool="tool",
            tags="",
        )
        assert s.tags == []

    def test_to_dict(self) -> None:
        s = AICommandSuggestion(
            command="git status",
            description="Show status",
            tool="git",
            tags=["status"],
        )
        d = s.to_dict()
        assert d["command"] == "git status"
        assert d["tool"] == "git"
        assert d["tags"] == ["status"]

    def test_to_entry_dict(self) -> None:
        s = AICommandSuggestion(
            command="git status",
            description="Show status",
            tool="git",
            tags=["status", "repo"],
        )
        d = s.to_entry_dict()
        assert d["command"] == "git status"
        assert d["tags"] == "status, repo"


class TestAIContext:
    """Tests for AIContext model."""

    def test_detect_returns_context(self) -> None:
        ctx = AIContext.detect()
        assert ctx.platform in ("windows", "linux", "macos")
        assert ctx.shell
        assert ctx.cwd

    def test_custom_context(self) -> None:
        ctx = AIContext(platform="linux", shell="zsh", cwd="/home/user")
        assert ctx.platform == "linux"
        assert ctx.shell == "zsh"
        assert ctx.cwd == "/home/user"


class TestParseSuggestions:
    """Tests for parse_suggestions function."""

    def test_valid_json(self) -> None:
        data = {
            "suggestions": [
                {
                    "tool": "git",
                    "command": "git status",
                    "description": "Show status",
                    "tags": ["status"],
                }
            ]
        }
        result = parse_suggestions(json.dumps(data))
        assert len(result) == 1
        assert result[0].command == "git status"

    def test_multiple_suggestions(self) -> None:
        data = {
            "suggestions": [
                {"tool": "git", "command": "git status", "description": "Status"},
                {"tool": "docker", "command": "docker ps", "description": "List"},
            ]
        }
        result = parse_suggestions(json.dumps(data))
        assert len(result) == 2

    def test_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_suggestions("not json")

    def test_not_object(self) -> None:
        with pytest.raises(TypeError, match="must be a JSON object"):
            parse_suggestions(json.dumps([1, 2, 3]))

    def test_missing_suggestions(self) -> None:
        with pytest.raises(TypeError, match="suggestions.*array"):
            parse_suggestions(json.dumps({"other": []}))

    def test_suggestions_not_array(self) -> None:
        with pytest.raises(TypeError, match="suggestions.*array"):
            parse_suggestions(json.dumps({"suggestions": "not array"}))

    def test_empty_suggestions(self) -> None:
        result = parse_suggestions(json.dumps({"suggestions": []}))
        assert result == []

    def test_invalid_suggestion_empty_command(self) -> None:
        data = {
            "suggestions": [
                {"tool": "git", "command": "", "description": "desc"}
            ]
        }
        with pytest.raises(ValueError, match="Suggestion 0 invalid"):
            parse_suggestions(json.dumps(data))

    def test_invalid_suggestion_not_object(self) -> None:
        data = {"suggestions": ["not object"]}
        with pytest.raises(TypeError, match="not an object"):
            parse_suggestions(json.dumps(data))

    def test_optional_fields(self) -> None:
        data = {
            "suggestions": [
                {"tool": "git", "command": "git status", "description": "Status"}
            ]
        }
        result = parse_suggestions(json.dumps(data))
        assert result[0].tags == []
        assert result[0].platform == ""


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_basic_prompt(self) -> None:
        prompt = build_system_prompt()
        assert "JSON" in prompt
        assert "suggestions" in prompt

    def test_with_context(self) -> None:
        ctx = AIContext(platform="windows", shell="powershell")
        prompt = build_system_prompt(ctx)
        assert "windows" in prompt
        assert "powershell" in prompt
