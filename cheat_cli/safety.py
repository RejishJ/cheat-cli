"""Deterministic safety classifier for command execution.

This module classifies commands as risky or non-risky based on pattern matching.
It is a confirmation-policy mechanism, NOT a security sandbox.
A command classified as non-risky can still be dangerous.
"""

from __future__ import annotations

import re
from typing import NamedTuple


class RiskMatch(NamedTuple):
    """A matched risky pattern in a command."""
    pattern: str
    description: str


# Patterns are matched case-insensitively against the full command string.
# Each tuple is (regex_pattern, human_description).
_RISKY_PATTERNS: list[tuple[str, str]] = [
    # File/directory destruction
    (r"\brm\s+.*-r", "Recursive file/directory removal"),
    (r"\brm\s+.*-f", "Forceful file removal"),
    (r"\bdel\s+.*(/s|/q)", "Recursive Windows file deletion"),
    (r"\brmdir\s+.*(/s|/q)", "Recursive Windows directory removal"),

    # Disk/filesystem operations
    (r"\bformat\b", "Disk formatting"),
    (r"\bdiskpart\b", "Disk partitioning"),
    (r"\bmkfs\b", "Filesystem creation"),
    (r"\bdd\s+", "Low-level disk copy/write"),

    # System operations
    (r"\bshutdown\b", "System shutdown"),
    (r"\breboot\b", "System reboot"),
    (r"\binit\s+[06]\b", "System runlevel change"),

    # Privilege escalation
    (r"\bsudo\b", "Privilege escalation (sudo)"),
    (r"\bchmod\s+.*-R", "Recursive permission change"),
    (r"\bchown\s+.*-R", "Recursive ownership change"),

    # Service management
    (r"\b(?:systemctl|service)\s+\S+\s+(?:stop|disable)\b", "Service disruption"),

    # Git destructive operations
    (r"\bgit\s+reset\s+.*--hard", "Destructive git reset"),
    (r"\bgit\s+clean\s+.*-f", "Destructive git clean"),
    (r"\bgit\s+push\s+.*--force", "Force git push"),
    (r"\bgit\s+push\s+.*-f\b", "Force git push"),

    # Docker cleanup
    (r"\bdocker\s+system\s+prune", "Docker system cleanup"),
    (r"\bdocker\s+rm\b", "Docker container removal"),
    (r"\bdocker\s+rmi\b", "Docker image removal"),

    # Package management (destructive)
    (r"\bpip\s+uninstall\b", "Python package removal"),
    (r"\bnpm\s+uninstall\b", "npm package removal"),

    # Network (potentially risky)
    (r"\biptables\b", "Firewall rule modification"),
    (r"\b(?:systemctl|service)\s+(?:stop|disable)\b", "Service disruption"),
]

# Pre-compiled patterns for performance
_COMPILED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pat, re.IGNORECASE), desc)
    for pat, desc in _RISKY_PATTERNS
]


def classify_command(command: str) -> list[RiskMatch]:
    """Classify a command and return all matching risky patterns.

    Args:
        command: The command string to classify.

    Returns:
        List of RiskMatch objects for each risky pattern found.
        Empty list means no risky patterns were matched (NOT that the command is safe).
    """
    matches: list[RiskMatch] = []
    for compiled, desc in _COMPILED:
        if compiled.search(command):
            matches.append(RiskMatch(pattern=compiled.pattern, description=desc))
    return matches


def is_risky_command(command: str) -> bool:
    """Return True if the command matches any risky pattern.

    This is a deterministic confirmation-policy check.
    It does NOT guarantee the command is safe if it returns False.
    """
    return len(classify_command(command)) > 0
