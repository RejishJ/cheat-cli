"""Tests for cheat_cli.config — Configuration management."""

from __future__ import annotations

from pathlib import Path

import pytest

from cheat_cli.config import (
    Config,
    _apply_env_overrides,
    _parse_bool,
    _parse_int,
    config_dir,
    config_path,
    is_offline,
    load_config_file,
    reset_config_file,
    resolve_config,
    save_config_file,
    set_offline_mode,
)


class TestConfigDataclass:
    """Tests for Config dataclass."""

    def test_defaults(self) -> None:
        c = Config()
        assert c.ai_provider == "openai-compatible"
        assert c.ai_model == ""
        assert c.ai_base_url == ""
        assert c.ai_timeout == 30
        assert c.offline is False

    def test_to_dict(self) -> None:
        c = Config(ai_provider="ollama", ai_model="llama3.2")
        d = c.to_dict()
        assert d["ai"]["provider"] == "ollama"
        assert d["ai"]["model"] == "llama3.2"

    def test_from_dict(self) -> None:
        data = {"ai": {"provider": "ollama", "model": "llama3", "timeout": "60"}}
        c = Config.from_dict(data)
        assert c.ai_provider == "ollama"
        assert c.ai_model == "llama3"
        assert c.ai_timeout == 60

    def test_from_dict_empty(self) -> None:
        c = Config.from_dict({})
        assert c.ai_provider == "openai-compatible"
        assert c.ai_timeout == 30


class TestParseHelpers:
    """Tests for _parse_int and _parse_bool."""

    def test_parse_int_valid(self) -> None:
        assert _parse_int("42", 0) == 42

    def test_parse_int_invalid(self) -> None:
        assert _parse_int("abc", 10) == 10

    def test_parse_bool_true(self) -> None:
        for val in ["true", "True", "TRUE", "yes", "1", "on"]:
            assert _parse_bool(val, False) is True

    def test_parse_bool_false(self) -> None:
        for val in ["false", "False", "no", "0", "off"]:
            assert _parse_bool(val, True) is False

    def test_parse_bool_invalid(self) -> None:
        # Default is True, so invalid value returns the default
        assert _parse_bool("maybe", True) is True
        assert _parse_bool("maybe", False) is False


class TestConfigPath:
    """Tests for config path resolution."""

    def test_config_dir_returns_path(self) -> None:
        d = config_dir()
        assert isinstance(d, Path)

    def test_config_path_in_config_dir(self) -> None:
        p = config_path()
        assert p.parent == config_dir()
        assert p.name == "config.ini"


class TestConfigFileOperations:
    """Tests for loading and saving config files."""

    def test_load_nonexistent_returns_defaults(self, tmp_path: Path) -> None:
        # Temporarily override config_path
        with pytest.MonkeyPatch.context() as m:
            m.setattr("cheat_cli.config.config_path", lambda: tmp_path / "config.ini")
            config = load_config_file()
            assert config.ai_provider == "openai-compatible"

    def test_save_and_load(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "config.ini"
        with pytest.MonkeyPatch.context() as m:
            m.setattr("cheat_cli.config.config_path", lambda: cfg_file)
            original = Config(ai_provider="ollama", ai_model="llama3", ai_timeout=60)
            save_config_file(original)
            loaded = load_config_file()
            assert loaded.ai_provider == "ollama"
            assert loaded.ai_model == "llama3"
            assert loaded.ai_timeout == 60

    def test_reset_removes_file(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / "config.ini"
        cfg_file.write_text("[ai]\nprovider = ollama\n")
        with pytest.MonkeyPatch.context() as m:
            m.setattr("cheat_cli.config.config_path", lambda: cfg_file)
            reset_config_file()
            assert not cfg_file.exists()

    def test_reset_nonexistent_no_error(self, tmp_path: Path) -> None:
        with pytest.MonkeyPatch.context() as m:
            m.setattr("cheat_cli.config.config_path", lambda: tmp_path / "nope.ini")
            reset_config_file()  # Should not raise


class TestEnvOverrides:
    """Tests for environment variable overrides."""

    def test_env_override_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CHEAT_AI_PROVIDER", "ollama")
        config = _apply_env_overrides(Config())
        assert config.ai_provider == "ollama"

    def test_env_override_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CHEAT_AI_TIMEOUT", "120")
        config = _apply_env_overrides(Config())
        assert config.ai_timeout == 120

    def test_env_override_offline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CHEAT_OFFLINE", "true")
        config = _apply_env_overrides(Config())
        assert config.offline is True


class TestResolveConfig:
    """Tests for full config resolution chain."""

    def test_defaults(self) -> None:
        config = resolve_config()
        assert config.ai_provider == "openai-compatible"

    def test_cli_overrides(self) -> None:
        config = resolve_config({"provider": "ollama", "model": "llama3"})
        assert config.ai_provider == "ollama"
        assert config.ai_model == "llama3"

    def test_cli_overrides_timeout(self) -> None:
        config = resolve_config({"timeout": "60"})
        assert config.ai_timeout == 60

    def test_cli_overrides_offline(self) -> None:
        config = resolve_config({"offline": "true"})
        assert config.offline is True

    def test_env_overrides_config_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CHEAT_AI_PROVIDER", "ollama")
        config = resolve_config()
        assert config.ai_provider == "ollama"


class TestOfflineMode:
    """Tests for global offline mode flag."""

    def test_default_offline(self) -> None:
        set_offline_mode(False)
        assert is_offline() is False

    def test_set_offline(self) -> None:
        set_offline_mode(True)
        assert is_offline() is True
        set_offline_mode(False)  # cleanup

    def test_offline_resets(self) -> None:
        set_offline_mode(True)
        set_offline_mode(False)
        assert is_offline() is False
