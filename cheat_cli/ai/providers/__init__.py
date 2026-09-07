"""AI provider implementations for cheat-cli."""

from __future__ import annotations

from .ollama import OllamaProvider
from .openai import OpenAICompatibleProvider

__all__ = ["OllamaProvider", "OpenAICompatibleProvider"]
