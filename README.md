# Cheat CLI

> A fast, terminal-first command-line tool for managing and retrieving your personal command-line knowledge.

A developer-focused cheat sheet for Linux developers who live in the terminal. Search, add, and manage your own command references without leaving the command line.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/license-proprietary-red.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/cheat-cli.svg)](https://pypi.org/project/cheat-cli/)

<!-- ![Demo](docs/assets/demo.gif) -->
<!-- Uncomment above line after recording a real demo GIF. See docs/assets/README.md for instructions. -->

## Why Cheat CLI?

You know the feeling. You're deep in a terminal session and you need that one `git` flag, that `find` syntax, or that `ffmpeg` command you used last week. You could open a browser, but that breaks your flow.

Cheat CLI keeps your most-used commands searchable from the terminal itself. No browser. No mouse. No context switching.

It's your personal command reference, built for developers who prefer staying in the terminal.

## Features

- **Instant search** — fuzzy-match across tools, commands, descriptions, and tags
- **Interactive add** — `cheat add` walks you through adding new entries
- **Safe delete** — `cheat delete` shows matches and asks for confirmation
- **User-writable data** — your cheats live outside `site-packages`, so they survive upgrades
- **Clean terminal output** — formatted tables via `tabulate`
- **Globally available** — install once, use everywhere with the `cheat` command
- **Sync-friendly** — your data is a single CSV file you can sync across machines

## Installation

```bash
pip install cheat-cli
```

Or install from source:

```bash
git clone https://github.com/RejishJ/cheat-cli.git
cd cheat-cli
pip install -e .
```

### Requirements

- Python 3.8+
- `pandas` (data handling)
- `tabulate` (terminal formatting)

## Quick Start

```bash
# Search for anything matching "git"
cheat git

# Show all entries
cheat all

# Add a new command interactively
cheat add

# Delete entries matching a query
cheat delete ffmpeg
```

## Usage

### Search

```bash
cheat <search-term>
```

Searches across all fields (tool, command, description, tags) and displays matching entries in a formatted table.

```bash
cheat git
```

Output:

```
╒═══════╤═══════════════╤══════════════════════════════════════╤══════════════════════╕
│ tool  │ command       │ description                          │ tags                 │
╞═══════╪═══════════════╪══════════════════════════════════════╪══════════════════════╡
│ git   │ git status    │ Show current git working tree status │ repo state branch    │
╘═══════╧═══════════════╧══════════════════════════════════════╧══════════════════════╛
```

### Show All

```bash
cheat all
```

Displays every entry in your cheat sheet.

### Add

```bash
cheat add
```

Interactive mode prompts you for:

- **Tool** — the tool or application name
- **Command** — the full command
- **Description** — what it does
- **Tags** — space-separated keywords for search

The entry is appended to your personal CSV file. Duplicate commands are rejected.

### Delete

```bash
cheat delete <query>
```

Finds commands matching the query, displays them, and asks for confirmation before removing them.

## How It Works

Cheat CLI stores your commands in a CSV file at:

```
~/.local/share/cheat-cli/commands.csv
```

On first run, this file is created from a bundled template with a starter set of commands. All subsequent searches, additions, and deletions operate on this user-local copy.

The bundled CSV (shipped with the package) is only used to bootstrap the user data directory — it is never modified directly.

### Data Format

The CSV has four columns:

| Column | Description |
|--------|-------------|
| `tool` | The tool or application name |
| `command` | The full command |
| `description` | What the command does |
| `tags` | Keywords for search matching |

### Example CSV

```csv
tool,command,description,tags
git,git status,Show current git working tree status,repo state branch
git,git log --oneline -10,Show last 10 commits in compact format,history log
find,find . -name "*.py",Find all Python files in current directory,search files
```

## Syncing Across Machines

Your cheat data is a single CSV file. To use the same cheats on multiple machines:

1. **Private Git repo** — commit `~/.local/share/cheat-cli/commands.csv` to a private repo and pull on each machine
2. **Cloud sync** — place the file in a synced folder (Dropbox, Syncthing, iCloud, etc.)
3. **Manual copy** — rsync or scp the file between machines

This keeps your data private and under your control.

## Project Structure

```
cheat-cli/
├── cheat_cli/
│   ├── __init__.py
│   ├── cli.py              # Main CLI logic
│   └── data/
│       └── commands.csv    # Bundled starter data
├── pyproject.toml           # Package metadata and build config
├── MANIFEST.in              # Data file inclusion for sdist
├── LICENSE
├── COPYRIGHT.md
├── README.md
└── docs/
    └── assets/              # Demo GIFs and screenshots
```

## Development

### Setup

```bash
git clone https://github.com/RejishJ/cheat-cli.git
cd cheat-cli
pip install -e .
```

### Running

```bash
cheat <search-term>
cheat all
cheat add
cheat delete <query>
```

### Code Style

The project is intentionally minimal. The core logic lives in `cli.py` (~100 lines). Keep it simple.

## Testing

```bash
# Run tests (when available)
pytest
```

> Testing is currently minimal. See the [Roadmap](#roadmap) for planned improvements.

## Roadmap

### Current

- [x] CSV-backed command storage
- [x] Search across all fields
- [x] Interactive add mode
- [x] Safe delete with confirmation
- [x] User-writable data directory
- [x] PyPI distribution

### Next

- [ ] Comprehensive test suite
- [ ] CI/CD pipeline
- [ ] Colored output improvements
- [ ] Export/import commands
- [ ] Tag-based filtering

### Future

- [ ] Multiple cheat sheet support
- [ ] Shell integration (bash/zsh completions)
- [ ] Remote cheat sheet sources
- [ ] Rich terminal UI with pagination
- [ ] Cross-platform support (macOS, Windows)

## Known Limitations

- Linux-focused data path (`~/.local/share/`)
- No built-in cross-machine sync (manual setup required)
- CSV format limits complex query capabilities
- No built-in backup/versioning

## Contributing

Cheat CLI is maintained by [Rejish J](https://github.com/RejishJ).

If you encounter a bug or have a feature suggestion, please [open an issue](https://github.com/RejishJ/cheat-cli/issues).

Code contributions and reuse require explicit written permission.

## License

Copyright (c) 2026 Rejish J. All rights reserved.

See [COPYRIGHT.md](COPYRIGHT.md) for details.

## Author

**Rejish J**
- GitHub: [RejishJ](https://github.com/RejishJ)
- Portfolio: [rejishjd-portfolio.vercel.app](https://rejishjd-portfolio.vercel.app/)
