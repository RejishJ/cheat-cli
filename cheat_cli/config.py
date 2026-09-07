"""Configuration management for cheat-cli.

Provides a layered configuration system with clear precedence:
  CLI arguments > environment variables > config file > built-in defaults.

Uses configparser with INI format (no external dependencies).
"""

from __future__ import annotations

import configparser
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Configuration file section/key constants
SECTION_AI = "ai"
KEY_PROVIDER = "provider"
KEY_MODEL = "model"
KEY_BASE_URL = "base_url"
KEY_TIMEOUT = "timeout"
KEY_OFFLINE = "offline"

# Environment variable to config key mapping
ENV_MAP: dict[str, tuple[str, str]] = {
    "CHEAT_AI_PROVIDER": (SECTION_AI, KEY_PROVIDER),
    "CHEAT_AI_MODEL": (SECTION_AI, KEY_MODEL),
    "CHEAT_AI_BASE_URL": (SECTION_AI, KEY_BASE_URL),
    "CHEAT_AI_TIMEOUT": (SECTION_AI, KEY_TIMEOUT),
    "CHEAT_OFFLINE": (SECTION_AI, KEY_OFFLINE),
}

# Built-in defaults
DEFAULTS: dict[str, dict[str, str]] = {
    SECTION_AI: {
        KEY_PROVIDER: "openai-compatible",
        KEY_MODEL: "",
        KEY_BASE_URL: "",
        KEY_TIMEOUT: "30",
        KEY_OFFLINE: "false",
    },
}


@dataclass
class Config:
    """Typed application configuration."""

    ai_provider: str = "openai-compatible"
    ai_model: str = ""
    ai_base_url: str = ""
    ai_timeout: int = 30
    offline: bool = False

    def to_dict(self) -> dict[str, dict[str, str]]:
        """Convert to configparser-compatible dict."""
        return {
            SECTION_AI: {
                KEY_PROVIDER: self.ai_provider,
                KEY_MODEL: self.ai_model,
                KEY_BASE_URL: self.ai_base_url,
                KEY_TIMEOUT: str(self.ai_timeout),
                KEY_OFFLINE: str(self.offline).lower(),
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, str]]) -> Config:
        """Create Config from configparser-style dict."""
        ai = data.get(SECTION_AI, {})
        return cls(
            ai_provider=ai.get(KEY_PROVIDER, DEFAULTS[SECTION_AI][KEY_PROVIDER]),
            ai_model=ai.get(KEY_MODEL, DEFAULTS[SECTION_AI][KEY_MODEL]),
            ai_base_url=ai.get(KEY_BASE_URL, DEFAULTS[SECTION_AI][KEY_BASE_URL]),
            ai_timeout=_parse_int(
                ai.get(KEY_TIMEOUT, DEFAULTS[SECTION_AI][KEY_TIMEOUT]), 30
            ),
            offline=_parse_bool(
                ai.get(KEY_OFFLINE, DEFAULTS[SECTION_AI][KEY_OFFLINE]), False
            ),
        )


def _parse_int(value: str, default: int) -> int:
    """Parse a string to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_bool(value: str, default: bool) -> bool:
    """Parse a string to bool, returning default on failure."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False
        return default
    return default


def config_dir() -> Path:
    """Return the platform-appropriate config directory for cheat-cli.

    Linux/macOS: ~/.config/cheat-cli/
    Windows: %APPDATA%/cheat-cli/
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "cheat-cli"
        return Path.home() / "AppData" / "Roaming" / "cheat-cli"

    # XDG_CONFIG_HOME or ~/.config
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "cheat-cli"
    return Path.home() / ".config" / "cheat-cli"


def config_path() -> Path:
    """Return the full path to the configuration file."""
    return config_dir() / "config.ini"


def load_config_file() -> Config:
    """Load configuration from the config file.

    Returns default Config if file doesn't exist or is malformed.
    """
    path = config_path()
    if not path.exists():
        return Config()

    parser = configparser.ConfigParser()
    try:
        parser.read(str(path), encoding="utf-8")
    except (configparser.Error, OSError):
        return Config()

    data: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        data[section] = dict(parser[section])

    return Config.from_dict(data)


def save_config_file(config: Config) -> None:
    """Save configuration to the config file."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    parser = configparser.ConfigParser()
    for section, values in config.to_dict().items():
        parser[section] = values

    with open(path, "w", encoding="utf-8") as f:
        parser.write(f)


def reset_config_file() -> None:
    """Reset configuration to defaults by removing the config file."""
    path = config_path()
    if path.exists():
        path.unlink()


def _apply_env_overrides(config: Config) -> Config:
    """Apply environment variable overrides to a config."""
    for env_var, (section, key) in ENV_MAP.items():
        value = os.environ.get(env_var)
        if value is None:
            continue

        if key == KEY_PROVIDER:
            config.ai_provider = value
        elif key == KEY_MODEL:
            config.ai_model = value
        elif key == KEY_BASE_URL:
            config.ai_base_url = value
        elif key == KEY_TIMEOUT:
            config.ai_timeout = _parse_int(value, config.ai_timeout)
        elif key == KEY_OFFLINE:
            config.offline = _parse_bool(value, config.offline)

    return config


def resolve_config(
    cli_overrides: dict[str, str | bool | None] | None = None,
) -> Config:
    """Resolve configuration with full precedence chain.

    Precedence (highest to lowest):
      1. CLI arguments
      2. Environment variables
      3. Config file
      4. Built-in defaults

    Args:
        cli_overrides: Dict of CLI-provided overrides.
            Keys: provider, model, base_url, timeout, offline.

    Returns:
        Fully resolved Config object.
    """
    # Layer 4: defaults
    config = Config()

    # Layer 3: config file
    file_config = load_config_file()
    config = Config(
        ai_provider=file_config.ai_provider,
        ai_model=file_config.ai_model,
        ai_base_url=file_config.ai_base_url,
        ai_timeout=file_config.ai_timeout,
        offline=file_config.offline,
    )

    # Layer 2: environment variables
    config = _apply_env_overrides(config)

    # Layer 1: CLI overrides
    if cli_overrides:
        if cli_overrides.get("provider") is not None:
            config.ai_provider = str(cli_overrides["provider"])
        if cli_overrides.get("model") is not None:
            config.ai_model = str(cli_overrides["model"])
        if cli_overrides.get("base_url") is not None:
            config.ai_base_url = str(cli_overrides["base_url"])
        if cli_overrides.get("timeout") is not None:
            config.ai_timeout = _parse_int(
                str(cli_overrides["timeout"]), config.ai_timeout
            )
        if cli_overrides.get("offline") is not None:
            config.offline = _parse_bool(
                str(cli_overrides["offline"]), config.offline
            )

    return config


# Global offline state (set by CLI --offline flag)
_offline_mode: bool = False


def set_offline_mode(enabled: bool) -> None:
    """Set the global offline mode flag."""
    global _offline_mode
    _offline_mode = enabled


def is_offline() -> bool:
    """Check if offline mode is active."""
    return _offline_mode
