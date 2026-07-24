"""
LLM Provider abstraction.

RULE: No file outside this module may import `langchain_google_genai`,
`openai`, `anthropic`, or any other LLM SDK directly. Agents (Slice 4+)
depend only on the `LLMProvider` protocol below, injected at construction
time. This is what "provider-agnostic" means in practice — swapping
Gemini for OpenAI is a one-line change in `get_llm_provider()`, not a
refactor across every agent.

Nothing called this in Slice 0-3. Slice 4 is the first real consumer:
ResumeIntelligenceAgent depends on `complete_structured`, never on a
concrete provider class or SDK.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    raw_metadata: dict = field(default_factory=dict)


class LLMProvider(ABC):
    """
    Contract every provider must satisfy.

    Two methods, matching the two shapes of call Talign's agents make:
      - `complete`: free-text response (used for narration/explanation,
        where strict schema validation isn't the point — see
        ResumeIntelligenceAgent.explain).
      - `complete_structured`: validated Pydantic model response (used
        anywhere the application depends on the SHAPE of the output,
        never on parsing free-form prose — see
        ResumeIntelligenceAgent.analyze). This is the method that makes
        "never parse arbitrary LLM prose" a real constraint rather than
        a docstring promise: callers get back a validated `T` instance
        or an exception, never a string they have to interpret.
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Send messages to the underlying model and return its free-text response."""
        raise NotImplementedError

    @abstractmethod
    async def complete_structured(
        self,
        messages: list[LLMMessage],
        *,
        response_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        """
        Send messages and return a response validated against
        `response_schema`. Implementations should use the provider's
        native structured-output/function-calling support where
        available; where not, the accepted fallback is "prompt for
        JSON, parse, validate" — but validation against `response_schema`
        is mandatory either way, not optional.

        Error contract callers rely on (see
        app.agents.resume_intelligence.agent for the consumer): raise
        `app.core.exceptions.InvalidStructuredOutputError` specifically
        when the response fails schema validation, and
        `app.core.exceptions.LLMProviderError` for anything else (network
        failure, timeout, rate limit). Callers use this distinction to
        decide whether a single re-prompt retry is worthwhile — it is for
        malformed output, it is not for a network-level failure.
        """
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """
    Google Gemini implementation.

    Talign's default provider (see ADR in docs/00_slice0_foundation.md).
    Both methods remain NotImplementedError stubs — this environment has
    no network path to generativelanguage.googleapis.com, so a real
    implementation here couldn't be verified and would be an untested
    guess. The full Resume Intelligence pipeline (extraction, alignment
    reasoning, scoring, persistence, retries, failure handling) is fully
    implemented and tested against `FakeLLMProvider`
    (tests/fakes.py) instead — see
    docs/04_slice4_resume_intelligence.md section H for why that's a
    deliberate, documented boundary rather than a gap.
    """

    def __init__(self, api_key: str | None, default_model: str) -> None:
        self._api_key = api_key
        self._default_model = default_model

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise NotImplementedError(
            "GeminiProvider.complete has no verified implementation in this "
            "environment — see class docstring."
        )

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        *,
        response_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        raise NotImplementedError(
            "GeminiProvider.complete_structured has no verified implementation in "
            "this environment — see class docstring."
        )


class OpenAIProvider(LLMProvider):
    """Stub — implemented only if/when we actually switch providers."""

    def __init__(self, api_key: str | None, default_model: str) -> None:
        self._api_key = api_key
        self._default_model = default_model

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise NotImplementedError("OpenAIProvider is a placeholder for future provider swap.")

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        *,
        response_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        raise NotImplementedError("OpenAIProvider is a placeholder for future provider swap.")


@lru_cache
def get_llm_provider() -> LLMProvider:
    """
    Factory returning the configured provider.

    This is the ONLY place in the codebase that branches on
    `settings.llm_provider`. Agents call `get_llm_provider()` (or receive
    it via dependency injection) and never know or care which concrete
    class they got.
    """
    if settings.llm_provider == "gemini":
        return GeminiProvider(
            api_key=settings.google_api_key,
            default_model=settings.llm_default_model,
        )
    if settings.llm_provider == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            default_model=settings.llm_default_model,
        )
    raise ValueError(f"Unsupported LLM provider configured: {settings.llm_provider}")
