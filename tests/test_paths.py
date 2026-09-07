"""Tests for cheat_cli.core.paths."""

import os
from pathlib import Path
from unittest.mock import patch

from cheat_cli.core.paths import data_dir, is_wsl, legacy_data_dir, user_csv_path


class TestDataDir:
    def test_linux_xdg(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "linux"
            with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}, clear=False):
                result = data_dir()
                assert result == Path("/custom/data/cheat-cli")

    def test_linux_default(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "linux"
            with patch.dict(os.environ, {}, clear=False):
                # Remove XDG_DATA_HOME if present
                env = os.environ.copy()
                env.pop("XDG_DATA_HOME", None)
                with patch.dict(os.environ, env, clear=True):
                    result = data_dir()
                    assert result == Path.home() / ".local" / "share" / "cheat-cli"

    def test_darwin(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "darwin"
            result = data_dir()
            assert result == Path.home() / "Library" / "Application Support" / "cheat-cli"

    def test_windows_with_localappdata(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "win32"
            with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}, clear=False):
                result = data_dir()
                assert result == Path("C:\\Users\\test\\AppData\\Local") / "cheat-cli"

    def test_windows_without_localappdata(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "win32"
            env = os.environ.copy()
            env.pop("LOCALAPPDATA", None)
            with patch.dict(os.environ, env, clear=True):
                result = data_dir()
                assert result == Path.home() / "AppData" / "Local" / "cheat-cli"


class TestUserCsvPath:
    def test_returns_csv_in_data_dir(self):
        result = user_csv_path()
        assert result.name == "commands.csv"
        assert result.parent == data_dir()


class TestIsWsl:
    def test_not_wsl_on_windows(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "win32"
            assert is_wsl() is False

    def test_not_wsl_on_darwin(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "darwin"
            assert is_wsl() is False

    def test_wsl_with_env_var(self):
        with patch("cheat_cli.core.paths.sys") as mock_sys:
            mock_sys.platform = "linux"
            with patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}, clear=False):
                assert is_wsl() is True


class TestLegacyDataDir:
    def test_returns_home_local_share(self):
        result = legacy_data_dir()
        assert result == Path.home() / ".local" / "share" / "cheat-cli"
