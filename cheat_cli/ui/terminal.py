"""Terminal utilities: TTY detection, color support, ANSI helpers."""

import os
import sys


def is_tty() -> bool:
    """Check if stdout is connected to a terminal."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def supports_color() -> bool:
    """Check if the terminal supports ANSI color codes.

    Respects NO_COLOR convention (https://no-color.org/).
    """
    if os.environ.get("NO_COLOR"):
        return False
    if not is_tty():
        return False
    # Windows Terminal and PowerShell 7 support ANSI
    if sys.platform == "win32":
        return os.environ.get("TERM") or os.environ.get("WT_SESSION") or os.environ.get("PSModulePath")
    return True


def colorize(text: str, code: str) -> str:
    """Wrap text in ANSI color escape codes if color is supported."""
    if not supports_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def red(text: str) -> str:
    """Color text red (for errors)."""
    return colorize(text, "91")


def green(text: str) -> str:
    """Color text green (for success)."""
    return colorize(text, "92")


def blue(text: str) -> str:
    """Color text blue (for info)."""
    return colorize(text, "94")


def bold(text: str) -> str:
    """Make text bold."""
    return colorize(text, "1")
