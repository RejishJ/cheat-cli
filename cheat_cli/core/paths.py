"""Platform-aware path resolution for cheat-cli data storage."""

import os
import sys
from pathlib import Path


def is_wsl() -> bool:
    """Detect if running inside Windows Subsystem for Linux."""
    if sys.platform != "linux":
        return False
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def data_dir() -> Path:
    """Return the platform-appropriate data directory for cheat-cli.

    Linux:      ~/.local/share/cheat-cli/   (or $XDG_DATA_HOME/cheat-cli/)
    WSL:        same as Linux
    macOS:      ~/Library/Application Support/cheat-cli/
    Windows:    %LOCALAPPDATA%/cheat-cli/
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "cheat-cli"
        return Path.home() / "AppData" / "Local" / "cheat-cli"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "cheat-cli"

    # Linux / WSL
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "cheat-cli"
    return Path.home() / ".local" / "share" / "cheat-cli"


def user_csv_path() -> Path:
    """Return the full path to the user's commands.csv file."""
    return data_dir() / "commands.csv"


def packaged_csv_path() -> Path:
    """Return the path to the bundled seed commands.csv inside the package."""
    from importlib.resources import files
    return files("cheat_cli").joinpath("data/commands.csv")
