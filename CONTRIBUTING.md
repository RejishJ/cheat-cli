# Contributing to cheat-cli

Thank you for considering contributing to cheat-cli.

## What Is This Project

cheat-cli is a terminal-first personal cheat sheet for developers. Search, add, and manage command references directly from the CLI.

## Development Setup

```bash
git clone https://github.com/RejishJ/cheat-cli.git
cd cheat-cli
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -e ".[dev]"
```

## Running the Project

```bash
cheat
cheat all
cheat add
cheat git
```

## Running Tests

The test suite is currently being established. Once available:

```bash
pytest
```

Until then, verify changes work by running the CLI commands manually after your modifications.

## Code Quality

- Keep changes focused and minimal
- Follow the existing code style
- Do not add unnecessary dependencies
- Do not commit API keys, tokens, passwords, or credentials
- Test your changes before submitting

## Branch Naming

Use descriptive branch names with a type prefix:

- `feat/<feature>` for new features
- `fix/<bug>` for bug fixes
- `refactor/<area>` for code restructuring
- `docs/<area>` for documentation
- `test/<area>` for test additions
- `chore/<area>` for maintenance tasks

Examples:

- `feat/cli-foundation`
- `fix/windows-storage`
- `docs/architecture`

## Commit Messages

Use clear, focused commit messages:

- `feat: add argparse-based CLI`
- `fix: correct Python version requirement`
- `docs: add changelog`
- `test: add storage round-trip tests`

Keep commits logically atomic. One commit per logical change.

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes in focused commits
3. Ensure tests pass (or describe manual testing)
4. Push your branch and open a PR
5. Fill out the PR template
6. Wait for review before merging

## Security

Do not commit secrets, API keys, tokens, or credentials. See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
