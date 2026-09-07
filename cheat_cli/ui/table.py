"""Table output formatting for cheat-cli entries."""

from __future__ import annotations

import sys

from tabulate import tabulate

from ..core.models import Entry
from .terminal import red


def print_entries(entries: list[Entry]) -> None:
    """Print entries as a formatted table.

    Args:
        entries: List of Entry objects to display.
    """
    if not entries:
        print(red("No results found."))
        return

    headers = ["tool", "command", "description", "tags"]
    rows = [[getattr(e, h) for h in headers] for e in entries]

    # Use plain format when not a TTY (piped output)
    tablefmt = "fancy_grid" if hasattr(sys.stdout, "isatty") and sys.stdout.isatty() else "simple"

    print(tabulate(rows, headers=headers, tablefmt=tablefmt))
