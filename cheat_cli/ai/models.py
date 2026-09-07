"""AI domain models for cheat-cli."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class AICommandSuggestion:
    """A command suggestion from an AI provider."""

    command: str
    description: str
    tool: str
    tags: list[str] = field(default_factory=list)
    platform: str = ""
    shell: str = ""

    def __post_init__(self) -> None:
        if not self.command or not self.command.strip():
            raise ValueError("command must not be empty")
        if not self.description or not self.description.strip():
            raise ValueError("description must not be empty")
        if not self.tool or not self.tool.strip():
            raise ValueError("tool must not be empty")
        if isinstance(self.tags, str):
            self.tags = [t.strip() for t in self.tags.split(",") if t.strip()]

    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            "command": self.command,
            "description": self.description,
            "tool": self.tool,
            "tags": self.tags,
            "platform": self.platform,
            "shell": self.shell,
        }

    def to_entry_dict(self) -> dict[str, str]:
        """Convert to Entry-compatible dict for display."""
        return {
            "tool": self.tool,
            "command": self.command,
            "description": self.description,
            "tags": ", ".join(self.tags) if self.tags else "",
        }


@dataclass
class AIContext:
    """Context information for AI requests."""

    platform: str = ""
    shell: str = ""
    cwd: str = ""

    @classmethod
    def detect(cls) -> AIContext:
        """Detect current platform and shell."""
        import os
        import platform
        import sys

        system = platform.system().lower()
        if sys.platform == "win32":
            plat = "windows"
            shell = os.environ.get("COMSPEC", "powershell.exe")
            shell = "powershell" if "powershell" in shell.lower() else "cmd"
        elif system == "darwin":
            plat = "macos"
            shell = os.environ.get("SHELL", "/bin/zsh")
            shell = "zsh" if "zsh" in shell else "bash"
        else:
            plat = "linux"
            shell = os.environ.get("SHELL", "/bin/bash")
            shell = "zsh" if "zsh" in shell else "bash"

        return cls(
            platform=plat,
            shell=shell,
            cwd=os.getcwd(),
        )


def parse_suggestions(response_text: str) -> list[AICommandSuggestion]:
    """Parse AI response text into structured suggestions.

    Expects JSON with a "suggestions" array.

    Raises:
        ValueError: If the response is malformed or contains invalid suggestions.
    """
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}") from e

    if not isinstance(data, dict):
        raise TypeError("Response must be a JSON object")

    suggestions_raw = data.get("suggestions")
    if not isinstance(suggestions_raw, list):
        raise TypeError("Response must contain a 'suggestions' array")

    suggestions = []
    for i, item in enumerate(suggestions_raw):
        try:
            if not isinstance(item, dict):
                raise TypeError(f"Suggestion {i} is not an object")
            suggestion = AICommandSuggestion(
                command=item.get("command", ""),
                description=item.get("description", ""),
                tool=item.get("tool", ""),
                tags=item.get("tags", []),
                platform=item.get("platform", ""),
                shell=item.get("shell", ""),
            )
            suggestions.append(suggestion)
        except ValueError as e:
            raise ValueError(f"Suggestion {i} invalid: {e}") from e

    return suggestions


def build_system_prompt(context: AIContext | None = None) -> str:
    """Build the system prompt for AI command suggestions."""
    prompt = (
        "You are a command-line assistant that suggests terminal commands.\n"
        "Return a JSON object with a 'suggestions' array.\n"
        "Each suggestion must have: command, description, tool.\n"
        "Optional: tags (array of strings), platform, shell.\n\n"
        "Example:\n"
        '{"suggestions": [{"tool": "git", "command": "git status", '
        '"description": "Show working tree status", "tags": ["git", "status"]}]}\n'
    )

    if context:
        prompt += f"\nUser environment: platform={context.platform}, shell={context.shell}\n"
        prompt += "Suggest commands appropriate for this environment.\n"

    return prompt
