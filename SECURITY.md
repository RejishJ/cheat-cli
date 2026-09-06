# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in Cheat CLI, please report it privately.

**Do not** open a public GitHub issue for security vulnerabilities.

Instead, contact the maintainer directly through [GitHub](https://github.com/RejishJ) with a description of the vulnerability.

## Response

The maintainer will acknowledge receipt within 72 hours and provide an update on the fix timeline.

## Scope

Cheat CLI is a local CLI tool that stores data in `~/.local/share/cheat-cli/`. It does not:

- Make network requests
- Store or transmit sensitive data
- Handle authentication
- Process user input beyond the local terminal

The primary security concern is ensuring the package distribution remains clean and that no malicious code is introduced through dependencies.

## Dependency Security

This project uses `pip` for dependency management. Dependencies are pinned in `pyproject.toml`. The project does not use a lockfile, but dependencies are minimal (`pandas`, `tabulate`).
