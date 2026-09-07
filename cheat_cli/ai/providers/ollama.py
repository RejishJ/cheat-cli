"""Ollama local provider for cheat-cli."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ..models import AICommandSuggestion, AIContext, build_system_prompt, parse_suggestions
from ..provider import ProviderRequestError, ProviderResponseError


class OllamaProvider:
    """Provider for local Ollama API."""

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._model = model or os.environ.get("CHEAT_AI_MODEL", "llama3.2")
        self._base_url = (
            base_url
            or os.environ.get("CHEAT_AI_BASE_URL", self.DEFAULT_BASE_URL)
        )
        self._timeout = timeout or float(os.environ.get("CHEAT_AI_TIMEOUT", "60"))

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def requires_api_key(self) -> bool:
        return False

    def suggest_commands(
        self,
        request: str,
        context: AIContext | None = None,
    ) -> list[AICommandSuggestion]:
        system_prompt = build_system_prompt(context)
        user_prompt = f"Suggest commands for: {request}"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 1000,
            },
        }

        url = f"{self._base_url.rstrip('/')}/api/chat"
        headers = {"Content-Type": "application/json"}

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
                "Is Ollama running? Check CHEAT_AI_BASE_URL or start Ollama."
            ) from e
        except TimeoutError:
            raise ProviderRequestError(
                f"Request timed out after {self._timeout}s.\n"
                "Ollama may be loading the model. Increase CHEAT_AI_TIMEOUT."
            ) from None

        try:
            content = response_data["message"]["content"]
        except KeyError as e:
            raise ProviderResponseError(
                "Unexpected response format from Ollama."
            ) from e

        return parse_suggestions(content)
