#!/usr/bin/env python3
"""CLI dispatcher for cheat-cli.

Provides the main entry point and argument parsing.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .cheat_service import CheatService
from .ui.table import print_entries
from .ui.terminal import blue, green, is_tty, red


def _get_version() -> str:
    """Return the version string."""
    return f"cheat-cli {__version__}"


def _try_launch_tui(service: CheatService, query: str = "") -> bool:
    """Attempt to launch the TUI. Returns True if launched, False otherwise."""
    if not is_tty():
        return False
    try:
        import importlib.util
        if importlib.util.find_spec("cheat_cli.ui.tui") is None:
            return False
    except (ImportError, ValueError):
        return False
    from .ui.tui.app import run_tui
    run_tui(service, query)
    return True


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="cheat",
        description=(
            "A terminal-first personal cheat sheet for developers.\n"
            "Search, add, and manage your own command references directly from the CLI."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  cheat ls              List all cheat entries\n"
            "  cheat ls git          Search entries matching 'git'\n"
            "  cheat search docker   Search entries matching 'docker'\n"
            "  cheat add             Add a new entry interactively\n"
            "  cheat rm git          Remove entries matching 'git'\n"
        ),
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=_get_version(),
    )

    subparsers = parser.add_subparsers(dest="command", help="available commands")

    # ls
    ls_parser = subparsers.add_parser(
        "ls",
        help="list cheat entries",
        description="List cheat entries, optionally filtered by a search query.",
    )
    ls_parser.add_argument("query", nargs="?", default=None, help="search query (optional)")

    # search
    search_parser = subparsers.add_parser(
        "search",
        help="search cheat entries",
        description="Search cheat entries across all fields.",
    )
    search_parser.add_argument("query", help="search query")

    # add
    subparsers.add_parser(
        "add",
        help="add a new cheat entry interactively",
        description="Interactively add a new cheat-sheet entry.",
    )

    # rm
    rm_parser = subparsers.add_parser(
        "rm",
        help="remove cheat entries",
        description="Remove cheat entries matching a query.",
    )
    rm_parser.add_argument("query", help="search query for entries to remove")

    # Compatibility: all -> ls
    all_parser = subparsers.add_parser(
        "all",
        help="[deprecated] use 'cheat ls'",
        description="[deprecated] Use 'cheat ls' instead.",
    )
    all_parser.add_argument("query", nargs="?", default=None, help=argparse.SUPPRESS)

    # Compatibility: delete -> rm
    delete_parser = subparsers.add_parser(
        "delete",
        help="[deprecated] use 'cheat rm'",
        description="[deprecated] Use 'cheat rm' instead.",
    )
    delete_parser.add_argument("query", nargs="?", default=None, help=argparse.SUPPRESS)

    return parser


def cmd_ls(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat ls' and 'cheat ls <query>'."""
    query = args.query or ""
    if _try_launch_tui(service, query):
        return 0

    entries = service.list_entries()
    if query:
        entries = service.search_filtered(entries, query)
    print_entries(entries)
    return 0


def cmd_search(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat search <query>'."""
    entries = service.list_entries()
    results = service.search_filtered(entries, args.query)
    print_entries(results)
    return 0


def cmd_add(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat add'."""
    print(blue("Interactive add mode"))
    tool = input("Tool: ").strip()
    command = input("Command: ").strip()
    description = input("Description: ").strip()
    tags = input("Tags: ").strip()

    if not command:
        print(red("Error: command cannot be empty."))
        return 1

    try:
        service.add_entry(tool, command, description, tags)
        print(green("Command added."))
        return 0
    except ValueError as e:
        print(red(f"Error: {e}"))
        return 1


def cmd_rm(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat rm <query>'."""
    entries = service.list_entries()
    matches = service.search_filtered(entries, args.query)

    if not matches:
        print(red("No match found."))
        return 1

    print_entries(matches)
    confirm = input("Delete these entries? (yes/no): ").lower()
    if confirm != "yes":
        print("Cancelled.")
        return 0

    deleted = service.delete_entries_by_values(matches)
    print(green(f"Deleted {deleted} {'entry' if deleted == 1 else 'entries'}."))
    return 0


def cmd_all(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat all' (compatibility alias for 'cheat ls')."""
    print(red("'cheat all' is deprecated. Use 'cheat ls' instead."), file=sys.stderr)
    return cmd_ls(args, service)


def cmd_delete(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat delete' (compatibility alias for 'cheat rm')."""
    print(red("'cheat delete' is deprecated. Use 'cheat rm' instead."), file=sys.stderr)
    if not args.query:
        print(red("Error: missing required argument 'query'."), file=sys.stderr)
        print("Usage: cheat rm <query>", file=sys.stderr)
        return 1
    return cmd_rm(args, service)


COMMAND_MAP = {
    "ls": cmd_ls,
    "search": cmd_search,
    "add": cmd_add,
    "rm": cmd_rm,
    "all": cmd_all,
    "delete": cmd_delete,
}


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the cheat CLI.

    Args:
        argv: Command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        service = CheatService()
        if _try_launch_tui(service):
            return 0
        parser.print_help()
        return 0

    handler = COMMAND_MAP.get(args.command)
    if handler is None:
        print(red(f"Error: unknown command '{args.command}'."), file=sys.stderr)
        print("Run 'cheat --help' for available commands.", file=sys.stderr)
        return 1

    service = CheatService()
    return handler(args, service)


if __name__ == "__main__":
    sys.exit(main())
