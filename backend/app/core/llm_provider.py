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

import structlog
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.exceptions import InvalidStructuredOutputError, LLMProviderError

T = TypeVar("T", bound=BaseModel)

logger = structlog.get_logger(__name__)


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
    Google Gemini implementation, built on `langchain_google_genai`
    (the only SDK this module is permitted to import — see module
    docstring).

    Talign's default provider (see ADR in docs/00_slice0_foundation.md).

    Design note: a fresh `ChatGoogleGenerativeAI` client is constructed
    per call rather than cached on `self`. Client construction is local
    object setup (no network I/O), and building fresh means `model` and
    `temperature` can vary per call — as the `LLMProvider` protocol
    requires — without any shared mutable client state to reason about.

    `complete_structured` uses LangChain's `with_structured_output`,
    which drives Gemini's native function-calling/JSON-mode structured
    output and validates the result against `response_schema` — this is
    the "provider's native structured-output support" the base class
    docstring asks for, not manual "prompt for JSON, parse" fallback.
    """

    def __init__(self, api_key: str | None, default_model: str) -> None:
        self._api_key = api_key
        self._default_model = default_model

    def _client(self, *, model: str | None, temperature: float) -> ChatGoogleGenerativeAI:
        if not self._api_key:
            raise LLMProviderError(
                "GOOGLE_API_KEY is not configured; GeminiProvider cannot make a call."
            )
        return ChatGoogleGenerativeAI(
            model=model or self._default_model,
            google_api_key=self._api_key,
            temperature=temperature,
        )

    @staticmethod
    def _to_langchain_messages(messages: list[LLMMessage]) -> list[BaseMessage]:
        role_map: dict[str, type[BaseMessage]] = {
            "system": SystemMessage,
            "user": HumanMessage,
            "assistant": AIMessage,
        }
        converted: list[BaseMessage] = []
        for message in messages:
            message_cls = role_map.get(message.role)
            if message_cls is None:
                raise LLMProviderError(f"Unsupported LLMMessage role for Gemini: {message.role!r}")
            converted.append(message_cls(content=message.content))
        return converted

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        client = self._client(model=model, temperature=temperature)
        lc_messages = self._to_langchain_messages(messages)
        try:
            result = await client.ainvoke(lc_messages)
        except LLMProviderError:
            raise
        except Exception as exc:
            raise LLMProviderError(f"Gemini completion call failed: {exc}") from exc
        return LLMResponse(
            content=result.content,
            model=model or self._default_model,
            raw_metadata=result.response_metadata or {},
        )

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        *,
        response_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        client = self._client(model=model, temperature=temperature)
        structured_client = client.with_structured_output(response_schema)
        lc_messages = self._to_langchain_messages(messages)
        try:
            result = await structured_client.ainvoke(lc_messages)
        except LLMProviderError:
            raise
        except (ValidationError, OutputParserException) as exc:
            # Schema-validation failure specifically — this is the case
            # ResumeIntelligenceAgent._complete_structured_with_retry
            # re-prompts once for. Must stay distinct from the broad
            # except below.
            logger.warning(
                "gemini_structured_output_validation_failed",
                schema=response_schema.__name__,
                error=str(exc),
            )
            raise InvalidStructuredOutputError(
                f"Gemini response did not match {response_schema.__name__}: {exc}"
            ) from exc
        except Exception as exc:
            raise LLMProviderError(f"Gemini structured completion call failed: {exc}") from exc

        if not isinstance(result, response_schema):
            # with_structured_output can, depending on method/version,
            # hand back a dict instead of a validated model instance.
            # Treat that the same as a validation failure rather than
            # silently trusting an unvalidated shape.
            raise InvalidStructuredOutputError(
                f"Gemini structured output for {response_schema.__name__} was not a "
                f"validated model instance (got {type(result).__name__})."
            )
        return result


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


# =============================================================================
# Embedding provider — Slice 6 (Knowledge Agent).
#
# Kept in this same file, not a new one: the module-level RULE above
# ("no file outside this module may import an LLM SDK directly") is
# about SDK-import containment, not about chat-completions specifically.
# Adding the embedding classes here preserves that single boundary
# exactly, rather than creating a second SDK-touching file to track.
# =============================================================================


class EmbeddingProvider(ABC):
    """
    Contract every embedding provider must satisfy. Two methods, matching
    Gemini's own asymmetric embedding design: a document being indexed
    and a question being asked are embedded slightly differently under
    the hood (`task_type`), which measurably improves retrieval quality
    over treating them identically — see `embed_documents` vs
    `embed_query` below.
    """

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of chunks being indexed. One call per document's chunks, not per chunk."""
        raise NotImplementedError

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single question at query time."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Identifies which model produced a given embedding. Part of the
        contract (not just GeminiEmbeddingProvider-specific) because
        KnowledgeDocumentService persists this as embedding provenance
        (KnowledgeDocument.embedding_model — see that model's docstring)
        against the abstract `EmbeddingProvider` type, never a concrete
        provider class, so a future second provider is a drop-in.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension this provider produces — persisted as embedding_dimension."""
        raise NotImplementedError


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini implementation, built on the same `langchain_google_genai`
    SDK GeminiProvider already uses.

    Model: `gemini-embedding-001` (stable, GA) — not the newer
    `gemini-embedding-2`, which is multimodal but still Preview status.
    This project already hit a real production issue from a `-preview`
    model's quota limits (Slice 4's GeminiProvider default), so a stable
    model is the deliberate choice for anything MVP-critical.

    Dimension: 768, via `output_dimensionality` — the model natively
    produces 3072-dim vectors, truncated via Matryoshka Representation
    Learning (Google's own technique for this model; truncating loses
    little quality per their documentation). 768 keeps KnowledgeChunk's
    `Vector(768)` column reasonably sized while leaving meaningful
    headroom below the model's max, in case retrieval quality ever
    warrants moving up to 1536 later — that's a re-embedding migration,
    not a breaking schema change in kind.
    """

    _MODEL = "gemini-embedding-001"
    _DIMENSION = 768

    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    def _client(self, *, task_type: str) -> GoogleGenerativeAIEmbeddings:
        if not self._api_key:
            raise LLMProviderError(
                "GOOGLE_API_KEY is not configured; GeminiEmbeddingProvider cannot make a call."
            )
        return GoogleGenerativeAIEmbeddings(
            model=self._MODEL,
            google_api_key=self._api_key,
            task_type=task_type,
            output_dimensionality=self._DIMENSION,
        )

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        client = self._client(task_type="retrieval_document")
        try:
            return await client.aembed_documents(texts)
        except LLMProviderError:
            raise
        except Exception as exc:
            raise LLMProviderError(f"Gemini embedding call failed: {exc}") from exc

    async def embed_query(self, text: str) -> list[float]:
        client = self._client(task_type="retrieval_query")
        try:
            return await client.aembed_query(text)
        except LLMProviderError:
            raise
        except Exception as exc:
            raise LLMProviderError(f"Gemini query embedding call failed: {exc}") from exc

    @property
    def model_name(self) -> str:
        return self._MODEL

    @property
    def dimension(self) -> int:
        return self._DIMENSION


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """
    Mirrors get_llm_provider()'s factory pattern exactly — the only
    place branching on which embedding provider is configured. Not
    branching on settings.llm_provider (that setting is chat-completion-
    specific); embeddings default to Gemini regardless, since no
    alternative embedding provider exists in this codebase yet. Adding
    one later is the same one-function change get_llm_provider() would
    need for a new chat provider.
    """
    return GeminiEmbeddingProvider(api_key=settings.google_api_key)