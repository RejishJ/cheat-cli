"""Tests for cheat_cli.ui.terminal."""

import os
from unittest.mock import patch

from cheat_cli.ui.terminal import blue, colorize, green, is_tty, red, supports_color


class TestIsTTY:
    def test_tty(self):
        with patch("cheat_cli.ui.terminal.sys") as mock_sys:
            mock_sys.stdout.isatty.return_value = True
            assert is_tty() is True

    def test_not_tty(self):
        with patch("cheat_cli.ui.terminal.sys") as mock_sys:
            mock_sys.stdout.isatty.return_value = False
            assert is_tty() is False

    def test_no_isatty(self):
        with patch("cheat_cli.ui.terminal.sys") as mock_sys:
            del mock_sys.stdout.isatty
            assert is_tty() is False


class TestSupportsColor:
    def test_no_color_env(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            assert supports_color() is False

    def test_not_tty_no_color(self):
        with patch("cheat_cli.ui.terminal.is_tty", return_value=False):
            assert supports_color() is False

    def test_tty_with_color(self):
        with patch("cheat_cli.ui.terminal.is_tty", return_value=True), \
             patch("cheat_cli.ui.terminal.sys") as mock_sys, \
             patch.dict(os.environ, {}, clear=True):
            mock_sys.platform = "linux"
            assert supports_color() is True


class TestColorize:
    def test_with_color_supported(self):
        with patch("cheat_cli.ui.terminal.supports_color", return_value=True):
            result = colorize("hello", "91")
            assert result == "\033[91mhello\033[0m"

    def test_without_color(self):
        with patch("cheat_cli.ui.terminal.supports_color", return_value=False):
            result = colorize("hello", "91")
            assert result == "hello"


class TestColorHelpers:
    def test_red(self):
        with patch("cheat_cli.ui.terminal.supports_color", return_value=True):
            assert red("error") == "\033[91merror\033[0m"

    def test_green(self):
        with patch("cheat_cli.ui.terminal.supports_color", return_value=True):
            assert green("ok") == "\033[92mok\033[0m"

    def test_blue(self):
        with patch("cheat_cli.ui.terminal.supports_color", return_value=True):
            assert blue("info") == "\033[94minfo\033[0m"
