"""Tests for cheat_cli.runner — cross-platform command runner."""

from __future__ import annotations

import unittest.mock

from cheat_cli.runner import RunResult, _needs_shell, run_command


class TestRunResult:
    def test_success_property(self) -> None:
        result = RunResult(command="echo hi", return_code=0)
        assert result.success is True

    def test_success_false_on_nonzero(self) -> None:
        result = RunResult(command="false", return_code=1)
        assert result.success is False

    def test_success_false_on_timeout(self) -> None:
        result = RunResult(command="sleep 10", timed_out=True)
        assert result.success is False

    def test_success_false_on_cancel(self) -> None:
        result = RunResult(command="echo hi", cancelled=True)
        assert result.success is False

    def test_success_false_on_error(self) -> None:
        result = RunResult(command="bad", error="not found")
        assert result.success is False

    def test_status_label_success(self) -> None:
        result = RunResult(command="echo hi", return_code=0)
        assert result.status_label == "Exit code: 0"

    def test_status_label_failure(self) -> None:
        result = RunResult(command="false", return_code=1)
        assert result.status_label == "Exit code: 1"

    def test_status_label_timeout(self) -> None:
        result = RunResult(command="sleep 10", timed_out=True, error="timed out")
        assert result.status_label == "Timed out"

    def test_status_label_cancelled(self) -> None:
        result = RunResult(command="echo hi", cancelled=True, error="cancelled")
        assert result.status_label == "Cancelled"

    def test_status_label_error(self) -> None:
        result = RunResult(command="bad", error="not found")
        assert result.status_label == "Error"


class TestNeedsShell:
    def test_pipe(self) -> None:
        assert _needs_shell("echo hi | grep h") is True

    def test_semicolon(self) -> None:
        assert _needs_shell("echo hi; echo bye") is True

    def test_ampersand(self) -> None:
        assert _needs_shell("echo hi && echo bye") is True

    def test_redirect(self) -> None:
        assert _needs_shell("echo hi > file.txt") is True

    def test_dollar(self) -> None:
        assert _needs_shell("echo $HOME") is True

    def test_simple_command(self) -> None:
        assert _needs_shell("echo hi") is False

    def test_command_with_args(self) -> None:
        assert _needs_shell("ls -la /tmp") is False

    def test_empty_string(self) -> None:
        assert _needs_shell("") is False


class TestRunCommand:
    def test_successful_command(self) -> None:
        result = run_command("echo hello")
        assert result.success is True
        assert result.stdout.strip() == "hello"
        assert result.return_code == 0

    def test_nonzero_exit(self) -> None:
        result = run_command("python -c \"import sys; sys.exit(1)\"")
        assert result.success is False
        assert result.return_code == 1

    def test_stderr_output(self) -> None:
        result = run_command("python -c \"import sys; sys.stderr.write('err\\n')\"")
        assert "err" in result.stderr

    def test_empty_command(self) -> None:
        result = run_command("")
        assert result.error == "Empty command"
        assert result.success is False

    def test_whitespace_command(self) -> None:
        result = run_command("   ")
        assert result.error == "Empty command"

    def test_missing_executable(self) -> None:
        result = run_command("nonexistent_command_xyz_123")
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower() or "error" in result.error.lower()

    def test_timeout(self) -> None:
        result = run_command("python -c \"import time; time.sleep(10)\"", timeout=0.1)
        assert result.timed_out is True
        assert result.success is False

    def test_command_preserved(self) -> None:
        cmd = "echo test"
        result = run_command(cmd)
        assert result.command == cmd

    def test_cwd_parameter(self) -> None:
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            if sys.platform == "win32":
                result = run_command("cmd /c cd", cwd=tmpdir)
            else:
                result = run_command("pwd", cwd=tmpdir)
            assert result.success is True
            if sys.platform != "win32":
                assert tmpdir in result.stdout

    def test_shell_metacharacters_use_shell(self) -> None:
        import sys
        if sys.platform == "win32":
            result = run_command("echo hello; echo world")
        else:
            result = run_command("echo hello | cat")
        assert result.success is True
        assert "hello" in result.stdout

    def test_simple_command_no_shell(self) -> None:
        with unittest.mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = unittest.mock.Mock(
                stdout="output", stderr="", returncode=0
            )
            run_command("echo hello")
            args = mock_run.call_args
            # Simple commands use shell=False with shlex.split
            assert args.kwargs.get("shell") is False
            assert args.args[0] == ["echo", "hello"]

    def test_simple_command_tokenized(self) -> None:
        with unittest.mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = unittest.mock.Mock(
                stdout="output", stderr="", returncode=0
            )
            run_command("git status --short")
            args = mock_run.call_args
            assert args.args[0] == ["git", "status", "--short"]
            assert args.kwargs.get("shell") is False

    def test_piped_command_uses_shell_false(self) -> None:
        with unittest.mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = unittest.mock.Mock(
                stdout="output", stderr="", returncode=0
            )
            run_command("echo hi | cat")
            args = mock_run.call_args
            assert args.kwargs.get("shell") is False
            cmd = args.args[0]
            # Uses explicit shell prefix
            assert cmd[0] in ("powershell", "/bin/sh")
            assert cmd[-1] == "echo hi | cat"

    def test_keyboard_interrupt(self) -> None:
        with unittest.mock.patch("subprocess.run", side_effect=KeyboardInterrupt):
            result = run_command("echo hi")
            assert result.cancelled is True
            assert result.success is False

    def test_os_error(self) -> None:
        with unittest.mock.patch("subprocess.run", side_effect=OSError("disk full")):
            result = run_command("echo hi")
            assert result.success is False
            assert "disk full" in result.error

    def test_file_not_found_error(self) -> None:
        with unittest.mock.patch(
            "subprocess.run", side_effect=FileNotFoundError("not found")
        ):
            result = run_command("bad_cmd")
            assert result.success is False
            assert "not found" in result.error


class TestRunCommandPlatforms:
    def test_windows_shell_syntax_command(self) -> None:
        with (
            unittest.mock.patch("sys.platform", "win32"),
            unittest.mock.patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = unittest.mock.Mock(
                stdout="", stderr="", returncode=0
            )
            run_command("echo hi | cat")
            args = mock_run.call_args
            cmd = args.args[0]
            assert cmd[0] == "powershell"
            assert cmd[-1] == "echo hi | cat"
            assert args.kwargs.get("shell") is False

    def test_posix_shell_syntax_command(self) -> None:
        with (
            unittest.mock.patch("sys.platform", "linux"),
            unittest.mock.patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = unittest.mock.Mock(
                stdout="", stderr="", returncode=0
            )
            run_command("echo hi | cat")
            args = mock_run.call_args
            cmd = args.args[0]
            assert cmd[0] == "/bin/sh"
            assert cmd[-1] == "echo hi | cat"
            assert args.kwargs.get("shell") is False

    def test_windows_simple_command_no_shell(self) -> None:
        with (
            unittest.mock.patch("sys.platform", "win32"),
            unittest.mock.patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = unittest.mock.Mock(
                stdout="", stderr="", returncode=0
            )
            run_command("dir /b")
            args = mock_run.call_args
            assert args.args[0] == ["dir", "/b"]
            assert args.kwargs.get("shell") is False

    def test_posix_simple_command_no_shell(self) -> None:
        with (
            unittest.mock.patch("sys.platform", "linux"),
            unittest.mock.patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = unittest.mock.Mock(
                stdout="", stderr="", returncode=0
            )
            run_command("ls -la /tmp")
            args = mock_run.call_args
            assert args.args[0] == ["ls", "-la", "/tmp"]
            assert args.kwargs.get("shell") is False
