"""OpenAI-compatible provider for cheat-cli."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ..models import AICommandSuggestion, AIContext, build_system_prompt, parse_suggestions
from ..provider import ProviderConfigError, ProviderRequestError, ProviderResponseError


class OpenAICompatibleProvider:
    """Provider for OpenAI-compatible API endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("CHEAT_AI_API_KEY", "")
        self._base_url = (
            base_url
            or os.environ.get("CHEAT_AI_BASE_URL", "https://api.openai.com/v1")
        )
        self._model = model or os.environ.get("CHEAT_AI_MODEL", "gpt-3.5-turbo")
        self._timeout = timeout or float(os.environ.get("CHEAT_AI_TIMEOUT", "30"))

    @property
    def name(self) -> str:
        return "openai-compatible"

    @property
    def requires_api_key(self) -> bool:
        return True

    def suggest_commands(
        self,
        request: str,
        context: AIContext | None = None,
    ) -> list[AICommandSuggestion]:
        if not self._api_key:
            raise ProviderConfigError(
                "API key is required for OpenAI-compatible provider.\n"
                "Set CHEAT_AI_API_KEY environment variable."
            )

        system_prompt = build_system_prompt(context)
        user_prompt = f"Suggest commands for: {request}"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
        }

        url = f"{self._base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except (OSError, UnicodeDecodeError):
                pass
            raise ProviderRequestError(
                f"HTTP {e.code}: {e.reason}\n{error_body}"
            ) from e
        except urllib.error.URLError as e:
            raise ProviderRequestError(
                f"Connection failed: {e.reason}\n"
                "Check your network connection or CHEAT_AI_BASE_URL."
            ) from e
        except TimeoutError:
            raise ProviderRequestError(
                f"Request timed out after {self._timeout}s.\n"
                "Check your network connection or increase CHEAT_AI_TIMEOUT."
            ) from None

        try:
            content = response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise ProviderResponseError(
                "Unexpected response format from provider."
            ) from e

        return parse_suggestions(content)
