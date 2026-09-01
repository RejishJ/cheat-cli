# cheat-cli

A **terminal-first personal cheat sheet** for Linux developers.  
Search, add, and manage your own command references directly from the CLI — no browser, no mouse.

Built with Python, designed for daily use by developers who live in the terminal.

---

## Features

- 🔍 **Instant search** across tools, commands, descriptions, and tags
- ➕ **Interactive add mode** (`cheat add`)
- 🗑️ **Safe delete** with confirmation (`cheat delete`)
- 📦 **User-writable data** stored outside `site-packages`
- 📊 **Clean terminal tables** with readable formatting
- 🚀 **Globally available CLI** after install
- 🐧 Linux-first, terminal-native workflow

---

## 🔄 Syncing Across Machines

Your personal cheat data is stored locally at:

~/.local/share/cheat-cli/commands.csv

To use the same cheats on multiple machines, you can:
- Keep this file in a private Git repository
- Or place it inside a cloud-synced folder (Dropbox, Syncthing, etc.)

This keeps your data private and under your control.


## 📦 Installation

Install from PyPI:

```bash
pip install cheat-cli
