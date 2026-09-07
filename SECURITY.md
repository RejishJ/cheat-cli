# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in cheat-cli, please report it responsibly.

**Do not publicly disclose sensitive vulnerabilities in issue reports.**

Instead, use one of these private channels:

- [GitHub Security Advisories](https://github.com/RejishJ/cheat-cli/security/advisories/new) (preferred, once enabled)
- Contact the maintainer directly through the repository

Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## What to Avoid

- Do not put API keys, passwords, tokens, or credentials in issue reports or PRs
- Do not publicly disclose vulnerabilities before a fix is available
- Do not commit secrets to the repository

## Scope

This security policy applies to the cheat-cli package distributed through PyPI and the source code in this repository.

cheat-cli currently stores data locally in CSV files and does not make network requests. Future versions may introduce AI provider integrations and network functionality, which will be addressed as the project evolves.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Security Best Practices for Users

- Keep your cheat-cli installation updated
- Review commands before running them, especially AI-generated commands
- Do not store sensitive information in cheat entries
