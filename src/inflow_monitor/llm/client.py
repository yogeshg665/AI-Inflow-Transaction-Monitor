"""Provider-agnostic LLM client used to generate monitoring narratives.

The client is intentionally optional. When no provider is configured the engine
operates in a fully deterministic mode, producing template-based narratives so
the system runs end to end without network access or credentials. A language
model may only enrich the narrative; it never changes the score or the decision.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from inflow_monitor.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMSettings:
    """Runtime settings for the LLM provider, sourced from the environment."""

    provider: str = "none"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    api_base: str = ""
    api_version: str = ""
    temperature: float = 0.1
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            provider=os.getenv("LLM_PROVIDER", "none").lower(),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("LLM_API_KEY", ""),
            api_base=os.getenv("LLM_API_BASE", ""),
            api_version=os.getenv("LLM_API_VERSION", ""),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        )

    @property
    def enabled(self) -> bool:
        return self.provider in {"openai", "azure_openai"} and bool(self.api_key)


class LLMClient:
    """Thin wrapper that yields a completion or signals deterministic fallback."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_env()

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    def summarize(self, system_prompt: str, user_prompt: str) -> str | None:
        """Return an LLM-generated summary, or None when disabled or on error.

        A None return is a normal control-flow signal that instructs callers to
        use their deterministic narrative builder instead.
        """
        if not self.settings.enabled:
            return None

        try:
            from openai import OpenAI  # imported lazily so it stays optional

            if self.settings.api_base:
                client = OpenAI(api_key=self.settings.api_key, base_url=self.settings.api_base)
            else:
                client = OpenAI(api_key=self.settings.api_key)

            response = client.chat.completions.create(
                model=self.settings.model,
                temperature=self.settings.temperature,
                timeout=self.settings.timeout_seconds,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:  # pragma: no cover - network/SDK dependent
            logger.warning("LLM summarization failed, using deterministic fallback: %s", exc)
            return None
