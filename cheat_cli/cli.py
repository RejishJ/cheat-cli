"""CLI dispatcher for cheat-cli.

Provides the main entry point and argument parsing.
"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import sys
from pathlib import Path

from . import __version__
from .cheat_service import CheatService
from .ui.table import print_entries
from .ui.terminal import blue, green, is_tty, red, yellow


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
            "  cheat ai \"find large files\"   Get AI command suggestions\n"
            "  cheat config          Show current configuration\n"
            "  cheat doctor          Diagnose installation issues\n"
        ),
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=_get_version(),
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=False,
        help="Run in offline mode (no network requests)",
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

    # ai
    ai_parser = subparsers.add_parser(
        "ai",
        help="get AI command suggestions",
        description="Request AI-powered command suggestions for a task.",
    )
    ai_parser.add_argument("request", help="description of what you want to do")
    ai_parser.add_argument(
        "--provider",
        choices=["openai-compatible", "ollama"],
        default=None,
        help="AI provider to use (default: config or CHEAT_AI_PROVIDER)",
    )
    ai_parser.add_argument(
        "--model",
        default=None,
        help="Model to use (default: config or CHEAT_AI_MODEL)",
    )
    ai_parser.add_argument(
        "--no-context",
        action="store_true",
        help="Do not send platform/shell context",
    )

    # config
    config_parser = subparsers.add_parser(
        "config",
        help="manage configuration",
        description="View or modify cheat-cli configuration.",
    )
    config_sub = config_parser.add_subparsers(dest="config_action", help="config actions")
    config_sub.add_parser("get", help="show all configuration values")
    config_set_parser = config_sub.add_parser("set", help="set a configuration value")
    config_set_parser.add_argument("key", help="configuration key (e.g., ai.provider)")
    config_set_parser.add_argument("value", help="value to set")
    config_sub.add_parser("reset", help="reset configuration to defaults")

    # doctor
    subparsers.add_parser(
        "doctor",
        help="diagnose installation issues",
        description="Check cheat-cli installation and configuration health.",
    )

    # export
    export_parser = subparsers.add_parser(
        "export",
        help="export commands to a file",
        description="Export command data to a CSV file.",
    )
    export_parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="output file path (default: stdout)",
    )

    # import
    import_parser = subparsers.add_parser(
        "import",
        help="import commands from a file",
        description="Import command data from a CSV file.",
    )
    import_parser.add_argument("file", help="input file path")

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


def cmd_ai(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat ai <request>'."""
    from .ai.models import AIContext
    from .ai.provider import ProviderError
    from .ai.registry import get_provider
    from .config import resolve_config

    request = args.request
    if not request:
        print(red("Error: missing request."), file=sys.stderr)
        print("Usage: cheat ai <request>", file=sys.stderr)
        return 1

    # Build config overrides from CLI args
    cli_overrides: dict[str, str | bool | None] = {}
    if args.provider:
        cli_overrides["provider"] = args.provider
    if args.model:
        cli_overrides["model"] = args.model

    config = resolve_config(cli_overrides)

    # Build provider kwargs from resolved config
    kwargs: dict[str, str | float] = {}
    if config.ai_model:
        kwargs["model"] = config.ai_model
    if config.ai_base_url:
        kwargs["base_url"] = config.ai_base_url
    if config.ai_timeout:
        kwargs["timeout"] = float(config.ai_timeout)

    try:
        provider = get_provider(name=config.ai_provider, **kwargs)
    except ProviderError as e:
        print(red(f"Error: {e}"), file=sys.stderr)
        return 1

    context = None if args.no_context else AIContext.detect()

    try:
        suggestions = provider.suggest_commands(request, context)
    except ProviderError as e:
        print(red(f"Error: {e}"), file=sys.stderr)
        return 1

    if not suggestions:
        print(yellow("No suggestions returned."))
        return 0

    print(blue(f"Suggestions for: {request}\n"))
    for i, s in enumerate(suggestions, 1):
        tags_str = f" [{', '.join(s.tags)}]" if s.tags else ""
        print(f"  {green(str(i))}. {s.tool} — {s.description}{tags_str}")
        print(f"     {s.command}")
        print()

    print(f"[dim]Review commands before use. Generated by {provider.name}.[/dim]")
    return 0


def cmd_config(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat config'."""
    from .config import (
        KEY_BASE_URL,
        KEY_MODEL,
        KEY_OFFLINE,
        KEY_PROVIDER,
        KEY_TIMEOUT,
        SECTION_AI,
        config_path,
        load_config_file,
        reset_config_file,
        resolve_config,
        save_config_file,
    )

    action = getattr(args, "config_action", None) or "get"

    if action == "get" or action is None:
        config = resolve_config()
        path = config_path()
        exists = path.exists()

        print(blue("Current configuration:\n"))
        print(f"  Config file: {path}")
        print(f"  Config exists: {'yes' if exists else 'no (using defaults)'}\n")

        print(f"  [{SECTION_AI}]")
        print(f"    {KEY_PROVIDER} = {config.ai_provider}")
        model_display = config.ai_model or "(not set)"
        print(f"    {KEY_MODEL} = {model_display}")
        base_url_display = config.ai_base_url or "(not set)"
        print(f"    {KEY_BASE_URL} = {base_url_display}")
        print(f"    {KEY_TIMEOUT} = {config.ai_timeout}")
        print(f"    {KEY_OFFLINE} = {config.offline}")

        # Show API key status (never reveal the actual key)
        api_key = os.environ.get("CHEAT_AI_API_KEY", "")
        key_status = "configured" if api_key else "not configured"
        print(f"\n  API key (env CHEAT_AI_API_KEY): {key_status}")

        # Show effective source for key values
        print(blue("\n  Environment variables:"))
        for env_var in ["CHEAT_AI_PROVIDER", "CHEAT_AI_MODEL", "CHEAT_AI_BASE_URL",
                        "CHEAT_AI_TIMEOUT", "CHEAT_AI_API_KEY", "CHEAT_OFFLINE"]:
            value = os.environ.get(env_var)
            if value is not None:
                if "KEY" in env_var:
                    print(f"    {env_var} = (set)")
                else:
                    print(f"    {env_var} = {value}")
            else:
                print(f"    {env_var} = (not set)")

        return 0

    elif action == "set":
        key = args.key
        value = args.value

        # Validate key
        valid_keys = {
            f"{SECTION_AI}.{KEY_PROVIDER}": "ai_provider",
            f"{SECTION_AI}.{KEY_MODEL}": "ai_model",
            f"{SECTION_AI}.{KEY_BASE_URL}": "ai_base_url",
            f"{SECTION_AI}.{KEY_TIMEOUT}": "ai_timeout",
            f"{SECTION_AI}.{KEY_OFFLINE}": "ai_offline",
        }

        if key not in valid_keys:
            print(red(f"Error: unknown configuration key '{key}'."), file=sys.stderr)
            print(f"Valid keys: {', '.join(sorted(valid_keys.keys()))}", file=sys.stderr)
            return 1

        # Load existing config, modify, save
        config = load_config_file()

        field_name = valid_keys[key]
        if field_name == "ai_provider":
            valid_providers = ["openai-compatible", "ollama"]
            if value not in valid_providers:
                print(
                    red(f"Error: invalid provider '{value}'. "
                        f"Valid providers: {', '.join(valid_providers)}"),
                    file=sys.stderr,
                )
                return 1
            config.ai_provider = value
        elif field_name == "ai_model":
            config.ai_model = value
        elif field_name == "ai_base_url":
            config.ai_base_url = value
        elif field_name == "ai_timeout":
            try:
                timeout_val = int(value)
                if timeout_val < 1:
                    raise ValueError
                config.ai_timeout = timeout_val
            except ValueError:
                print(
                    red("Error: timeout must be a positive integer."),
                    file=sys.stderr,
                )
                return 1
        elif field_name == "ai_offline":
            config.offline = value.lower() in ("true", "yes", "1", "on")

        save_config_file(config)
        print(green(f"Set {key} = {value}"))
        return 0

    elif action == "reset":
        reset_config_file()
        print(green("Configuration reset to defaults."))
        return 0

    else:
        print(red(f"Error: unknown config action '{action}'."), file=sys.stderr)
        return 1


def cmd_doctor(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat doctor'."""
    from .config import config_path, resolve_config
    from .core.paths import data_dir, user_csv_path

    issues = 0
    warnings = 0

    print(blue("cheat-cli doctor\n"))

    # 1. Python version
    py_ver = platform.python_version()
    py_min = "3.9"
    print(f"  Python version: {py_ver}")
    # Simple version comparison
    py_parts = tuple(int(x) for x in py_ver.split(".")[:2])
    if py_parts >= (3, 9):
        print(f"    {green('✓ OK')} — meets minimum requirement ({py_min}+)")
    else:
        print(f"    {red('✗ Error')} — requires Python {py_min}+, found {py_ver}")
        issues += 1

    # 2. cheat-cli version
    print(f"\n  cheat-cli version: {__version__}")
    print(f"    {green('✓ OK')}")

    # 3. Data directory
    data_directory = data_dir()
    print(f"\n  Data directory: {data_directory}")
    if data_directory.exists():
        print(f"    {green('✓ OK')} — exists")
    else:
        print(f"    {yellow('! Warning')} — does not exist (will be created on first use)")
        warnings += 1

    # 4. Command file
    csv_file = user_csv_path()
    print(f"\n  Command file: {csv_file}")
    if csv_file.exists():
        try:
            from .core.storage import load_entries
            entries = load_entries(csv_file)
            print(f"    {green('✓ OK')} — {len(entries)} commands loaded")
        except (OSError, ValueError) as e:
            print(f"    {red('✗ Error')} — {e}")
            issues += 1
    else:
        print(f"    {yellow('! Warning')} — does not exist (will be seeded on first use)")
        warnings += 1

    # 5. Config file
    cfg_path = config_path()
    print(f"\n  Config file: {cfg_path}")
    if cfg_path.exists():
        print(f"    {green('✓ OK')} — exists")
    else:
        print(f"    {yellow('! Warning')} — not found (using defaults)")
        warnings += 1

    # 6. Configuration values
    config = resolve_config()
    print("\n  Configuration:")
    print(f"    AI provider: {config.ai_provider}")
    print(f"    AI model: {config.ai_model or '(not set)'}")
    print(f"    AI base URL: {config.ai_base_url or '(not set)'}")
    print(f"    AI timeout: {config.ai_timeout}s")
    print(f"    Offline mode: {config.offline}")

    # 7. API key check (only for cloud providers)
    if config.ai_provider != "ollama":
        api_key = os.environ.get("CHEAT_AI_API_KEY", "")
        if api_key:
            print(f"\n  API key: {green('✓ configured')}")
        else:
            print(f"\n  API key: {yellow('! not configured')}")
            print("    Set CHEAT_AI_API_KEY to use AI features.")
            warnings += 1
    else:
        print(f"\n  API key: {blue('(not required for Ollama)')}")

    # 8. Ollama check (if selected)
    if config.ai_provider == "ollama":
        print("\n  Ollama connectivity:")
        try:
            import urllib.error
            import urllib.request

            base_url = config.ai_base_url or "http://localhost:11434"
            req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    print(f"    {green('✓ OK')} — Ollama is reachable at {base_url}")
                else:
                    print(f"    {yellow('! Warning')} — unexpected response from Ollama")
                    warnings += 1
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            print(f"    {yellow('! Warning')} — cannot reach Ollama: {e}")
            print("    Ensure Ollama is running at the configured base URL.")
            warnings += 1

    # 9. Write permissions
    print("\n  Write permissions:")
    if os.access(data_directory, os.W_OK) or not data_directory.exists():
        print(f"    {green('✓ OK')} — data directory is writable")
    else:
        print(f"    {red('✗ Error')} — data directory is not writable")
        issues += 1

    # Summary
    print(f"\n{'─' * 40}")
    if issues == 0 and warnings == 0:
        print(green("  All checks passed."))
    elif issues == 0:
        print(yellow(f"  {warnings} warning(s), no errors."))
    else:
        print(red(f"  {issues} error(s), {warnings} warning(s)."))

    return 1 if issues > 0 else 0


def cmd_export(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat export [file]'."""
    from .core.models import CSV_FIELDS

    try:
        entries = service.list_entries()
    except (OSError, ValueError) as e:
        print(red(f"Error: {e}"), file=sys.stderr)
        return 1

    if args.file:
        output_path = Path(args.file)
        # Check if file exists
        if output_path.exists():
            confirm = input(f"File '{output_path}' exists. Overwrite? (yes/no): ").lower()
            if confirm != "yes":
                print("Cancelled.")
                return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_dict())
        print(green(f"Exported {len(entries)} commands to {output_path}"))
    else:
        # Export to stdout
        writer = csv.DictWriter(sys.stdout, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.to_dict())

    return 0


def cmd_import(args: argparse.Namespace, service: CheatService) -> int:
    """Handle 'cheat import <file>'."""
    from .core.models import Entry
    from .core.storage import load_entries as storage_load_entries
    from .core.storage import save_entries as storage_save_entries
    from .core.storage import user_csv_path

    _IMPORT_REQUIRED = {"tool", "command", "description", "tags"}

    input_path = Path(args.file)
    if not input_path.exists():
        print(red(f"Error: file not found: {input_path}"), file=sys.stderr)
        return 1

    # Step 1: Read and validate import file
    try:
        import_entries: list[Entry] = []
        with open(input_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                print(red("Error: empty CSV file."), file=sys.stderr)
                return 1

            missing = _IMPORT_REQUIRED - set(reader.fieldnames)
            if missing:
                print(
                    red(f"Error: CSV missing required columns: {', '.join(sorted(missing))}"),
                    file=sys.stderr,
                )
                return 1

            for row_num, row in enumerate(reader, start=2):
                try:
                    tool = row.get("tool", "").strip()
                    command = row.get("command", "").strip()
                    description = row.get("description", "").strip()
                    tags = row.get("tags", "").strip()

                    if not command:
                        print(
                            yellow(f"Warning: row {row_num} has empty command, skipping."),
                            file=sys.stderr,
                        )
                        continue

                    entry = Entry(
                        tool=tool,
                        command=command,
                        description=description,
                        tags=tags,
                        id=row.get("id", "").strip(),
                        platform=row.get("platform", "").strip(),
                        shell=row.get("shell", "").strip(),
                        source=row.get("source", "").strip() or "user",
                        created_at=row.get("created_at", "").strip(),
                        updated_at=row.get("updated_at", "").strip(),
                    )
                    import_entries.append(entry)
                except (KeyError, ValueError) as e:
                    print(
                        yellow(f"Warning: row {row_num} malformed, skipping: {e}"),
                        file=sys.stderr,
                    )
    except (OSError, csv.Error) as e:
        print(red(f"Error reading file: {e}"), file=sys.stderr)
        return 1

    if not import_entries:
        print(yellow("No valid entries found in import file."))
        return 0

    # Step 2: Load existing entries
    try:
        existing_entries = storage_load_entries()
    except (OSError, ValueError):
        existing_entries = []

    # Step 3: Determine changes (skip duplicates by command string)
    existing_commands = {e.command for e in existing_entries}
    to_add = [e for e in import_entries if e.command not in existing_commands]
    skipped = len(import_entries) - len(to_add)

    if not to_add:
        print(yellow("All entries already exist. Nothing to import."))
        return 0

    # Step 4: Atomic write
    merged = existing_entries + to_add
    try:
        storage_save_entries(merged, user_csv_path())
    except (OSError, ValueError) as e:
        print(red(f"Error writing data: {e}"), file=sys.stderr)
        return 1

    print(green(f"Imported {len(to_add)} new commands."))
    if skipped > 0:
        print(yellow(f"Skipped {skipped} duplicate(s)."))
    return 0


COMMAND_MAP = {
    "ls": cmd_ls,
    "search": cmd_search,
    "add": cmd_add,
    "rm": cmd_rm,
    "all": cmd_all,
    "delete": cmd_delete,
    "ai": cmd_ai,
    "config": cmd_config,
    "doctor": cmd_doctor,
    "export": cmd_export,
    "import": cmd_import,
}


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the cheat CLI.

    Args:
        argv: Command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    from .config import set_offline_mode

    parser = build_parser()
    args = parser.parse_args(argv)

    # Set offline mode if requested
    if getattr(args, "offline", False):
        set_offline_mode(True)

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
