"""Tests for cheat_cli.ui.clipboard — cross-platform clipboard abstraction."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cheat_cli.ui.clipboard import ClipboardError, copy_to_clipboard


class TestCopyToClipboard:
    def test_copy_on_windows(self) -> None:
        with patch("cheat_cli.ui.clipboard.sys") as mock_sys:
            mock_sys.platform = "win32"
            with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                copy_to_clipboard("docker compose up -d")
                mock_run.assert_called_once()
                args = mock_run.call_args
                assert args[0][0] == ["clip"]
                assert args[1]["input"] == "docker compose up -d".encode("utf-16-le")

    def test_copy_on_macos(self) -> None:
        with patch("cheat_cli.ui.clipboard.sys") as mock_sys:
            mock_sys.platform = "darwin"
            with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                copy_to_clipboard("git status")
                mock_run.assert_called_once()
                args = mock_run.call_args
                assert args[0][0] == ["pbcopy"]
                assert args[1]["input"] == b"git status"

    def test_copy_on_linux_with_xclip(self) -> None:
        with patch("cheat_cli.ui.clipboard.sys") as mock_sys:
            mock_sys.platform = "linux"
            with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                copy_to_clipboard("kubectl get pods")
                mock_run.assert_called_once()
                args = mock_run.call_args
                assert args[0][0] == ["xclip", "-selection", "clipboard"]
                assert args[1]["input"] == b"kubectl get pods"

    def test_copy_on_linux_fallback_to_xsel(self) -> None:
        with patch("cheat_cli.ui.clipboard.sys") as mock_sys:
            mock_sys.platform = "linux"
            with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
                # First call (xclip) raises FileNotFoundError, second (xsel) succeeds
                mock_run.side_effect = [
                    FileNotFoundError(),
                    MagicMock(returncode=0),
                ]
                copy_to_clipboard("echo hello")
                assert mock_run.call_count == 2
                args = mock_run.call_args_list[1]
                assert args[0][0] == ["xsel", "--clipboard", "--input"]

    def test_copy_empty_string_is_noop(self) -> None:
        with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
            copy_to_clipboard("")
            mock_run.assert_not_called()

    def test_clipboard_os_error_raises(self) -> None:
        with patch("cheat_cli.ui.clipboard.sys") as mock_sys:
            mock_sys.platform = "win32"
            with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
                mock_run.side_effect = OSError("no clip")
                with pytest.raises(ClipboardError, match="Clipboard unavailable"):
                    copy_to_clipboard("test")

    def test_clipboard_nonzero_exit_raises(self) -> None:
        with patch("cheat_cli.ui.clipboard.sys") as mock_sys:
            mock_sys.platform = "win32"
            with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)
                with pytest.raises(ClipboardError, match="clip command failed"):
                    copy_to_clipboard("test")

    def test_linux_no_clipboard_utility_raises(self) -> None:
        with patch("cheat_cli.ui.clipboard.sys") as mock_sys:
            mock_sys.platform = "linux"
            with patch("cheat_cli.ui.clipboard.subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError()
                with pytest.raises(ClipboardError, match="No clipboard utility found"):
                    copy_to_clipboard("test")
