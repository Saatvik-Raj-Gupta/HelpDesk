from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.config import Settings


class LLMProvider(Protocol):
    def generate_text(self, prompt: str, *, temperature: float = 0.2) -> str:
        ...

    def health_check(self) -> dict[str, object]:
        ...


class StubProvider:
    def generate_text(self, prompt: str, *, temperature: float = 0.2) -> str:
        return "Stub provider active; Gemini generation is disabled."

    def health_check(self) -> dict[str, object]:
        return {"ok": True, "provider": "stub", "message": "Stub provider is active."}


@dataclass
class GeminiProvider:
    api_key: str | None
    model: str

    def __post_init__(self) -> None:
        self._client: object | None = None

    def _get_client(self) -> object:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Add it to your .env file before calling the Gemini provider.")

        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_text(self, prompt: str, *, temperature: float = 0.2) -> str:
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"temperature": temperature},
        )
        return getattr(response, "text", str(response))

    def health_check(self) -> dict[str, object]:
        try:
            self.generate_text("Reply with OK.", temperature=0.0)
            return {"ok": True, "provider": "gemini", "model": self.model, "message": "Gemini connectivity check passed."}
        except Exception as exc:  # pragma: no cover - surfaced to UI/logging
            return {
                "ok": False,
                "provider": "gemini",
                "model": self.model,
                "message": f"Gemini connectivity check failed: {exc}",
            }


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider.lower() != "gemini":
        return StubProvider()
    return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
