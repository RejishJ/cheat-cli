"""Cross-platform command runner for cheat-cli.

Executes commands with timeout protection and structured result reporting.
The caller is responsible for ensuring the user explicitly initiated execution.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class RunResult:
    """Structured result of a command execution."""
    command: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    timed_out: bool = False
    cancelled: bool = False
    error: str | None = None

    @property
    def success(self) -> bool:
        """Return True if the command completed successfully."""
        return self.return_code == 0 and not self.timed_out and not self.cancelled and not self.error

    @property
    def status_label(self) -> str:
        """Human-readable status label."""
        if self.cancelled:
            return "Cancelled"
        if self.timed_out:
            return "Timed out"
        if self.error:
            return "Error"
        return f"Exit code: {self.return_code}"


def _get_shell() -> list[str]:
    """Return the appropriate shell for the current platform.

    Returns a command prefix suitable for subprocess.run().
    On Windows: powershell -NoLogo -NoProfile -Command
    On Linux/macOS: /bin/sh -c
    """
    if sys.platform == "win32":
        return ["powershell", "-NoLogo", "-NoProfile", "-Command"]
    return ["/bin/sh", "-c"]


def _needs_shell(command: str) -> bool:
    """Determine if a command requires shell interpretation.

    Commands containing shell metacharacters need a shell.
    Simple commands can be split into argv directly.
    """
    shell_chars = {"|", "&", ";", ">", "<", "$", "`", "(", "{", "!"}
    return any(c in command for c in shell_chars)


def run_command(
    command: str,
    *,
    timeout: float = 30.0,
    cwd: str | None = None,
) -> RunResult:
    """Execute a command and return a structured result.

    Args:
        command: The command string to execute.
        timeout: Maximum execution time in seconds.
        cwd: Working directory for the command.

    Returns:
        RunResult with stdout, stderr, return code, and status flags.
    """
    if not command or not command.strip():
        return RunResult(command=command, error="Empty command")

    if _needs_shell(command):
        shell_cmd = _get_shell() + [command]
        use_shell = False
    else:
        shell_cmd = shlex.split(command)
        use_shell = False

    try:
        process = subprocess.run(
            shell_cmd,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )
        return RunResult(
            command=command,
            stdout=process.stdout,
            stderr=process.stderr,
            return_code=process.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            command=command,
            timed_out=True,
            error=f"Command timed out after {timeout}s",
        )
    except FileNotFoundError as e:
        return RunResult(
            command=command,
            error=f"Command not found: {e}",
        )
    except OSError as e:
        return RunResult(
            command=command,
            error=f"Execution error: {e}",
        )
    except KeyboardInterrupt:
        return RunResult(
            command=command,
            cancelled=True,
            error="Cancelled by user",
        )
