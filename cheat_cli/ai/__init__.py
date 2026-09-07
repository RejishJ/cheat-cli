"""AI provider architecture for cheat-cli.

Provides an extensible AI-powered command suggestion system
with a clean provider abstraction.
"""

from __future__ import annotations

from .models import AICommandSuggestion, AIContext
from .provider import AIProvider, ProviderError
from .registry import get_provider, list_providers
from .service import AIService

__all__ = [
    "AICommandSuggestion",
    "AIContext",
    "AIProvider",
    "AIService",
    "ProviderError",
    "get_provider",
    "list_providers",
]
