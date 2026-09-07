"""Cross-platform clipboard abstraction for cheat-cli."""

from __future__ import annotations

import subprocess
import sys


class ClipboardError(Exception):
    """Raised when a clipboard operation fails."""


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard.

    Uses platform-specific commands:
    - Windows: clip
    - macOS: pbcopy
    - Linux: xclip (falls back to xsel)

    Raises:
        ClipboardError: If the clipboard operation fails.
    """
    if not text:
        return

    try:
        if sys.platform == "win32":
            _copy_windows(text)
        elif sys.platform == "darwin":
            _copy_macos(text)
        else:
            _copy_linux(text)
    except OSError as e:
        raise ClipboardError(f"Clipboard unavailable: {e}") from e


def _copy_windows(text: str) -> None:
    """Copy text using Windows clip command."""
    process = subprocess.run(
        ["clip"],
        input=text.encode("utf-16-le"),
        check=True,
        capture_output=True,
    )
    if process.returncode != 0:
        raise ClipboardError("clip command failed")


def _copy_macos(text: str) -> None:
    """Copy text using macOS pbcopy command."""
    process = subprocess.run(
        ["pbcopy"],
        input=text.encode("utf-8"),
        check=True,
        capture_output=True,
    )
    if process.returncode != 0:
        raise ClipboardError("pbcopy command failed")


def _copy_linux(text: str) -> None:
    """Copy text using xclip, falling back to xsel."""
    try:
        process = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        if process.returncode != 0:
            raise ClipboardError("xclip command failed")
    except FileNotFoundError:
        try:
            process = subprocess.run(
                ["xsel", "--clipboard", "--input"],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            if process.returncode != 0:
                raise ClipboardError("xsel command failed")
        except FileNotFoundError:
            raise ClipboardError("No clipboard utility found (install xclip or xsel)") from None
