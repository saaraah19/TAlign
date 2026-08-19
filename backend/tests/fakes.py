"""
FakeLLMProvider — test double for LLMProvider.

Lets the full Resume Intelligence pipeline (agent orchestration, retry
logic, failure handling) be exercised end-to-end with zero network
dependency. Configure `structured_responses` with a queue of either
valid Pydantic instances (success) or exceptions to raise (simulating
provider failure or schema-validation failure) — the fake pops one per
call, in order, so a test can script "first call fails, retry succeeds"
scenarios precisely.
"""

from collections import deque
from typing import TypeVar

from pydantic import BaseModel

from app.core.llm_provider import EmbeddingProvider, LLMMessage, LLMProvider, LLMResponse

T = TypeVar("T", bound=BaseModel)


class FakeLLMProvider(LLMProvider):
    def __init__(
        self,
        *,
        structured_responses: list[BaseModel | Exception] | None = None,
        text_response: str | LLMResponse | Exception = "This is a fake explanation.",
    ) -> None:
        self._structured_queue: deque = deque(structured_responses or [])
        self._text_response = text_response
        self.calls: list[list[LLMMessage]] = []

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        self.calls.append(messages)
        if isinstance(self._text_response, Exception):
            raise self._text_response
        if isinstance(self._text_response, LLMResponse):
            return self._text_response
        return LLMResponse(content=self._text_response, model="fake-model")

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        *,
        response_schema: type[T],
        model: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        self.calls.append(messages)
        if not self._structured_queue:
            raise AssertionError("FakeLLMProvider: no more queued structured responses.")
        item = self._structured_queue.popleft()
        if isinstance(item, Exception):
            raise item
        return item  # type: ignore[return-value]


class FakeEmbeddingProvider(EmbeddingProvider):
    """
    Test double for EmbeddingProvider — same "configure a queued
    response, real behavior otherwise" philosophy as FakeLLMProvider.
    `document_vectors` / `query_vector` can each be a fixed value or an
    Exception to simulate a provider failure. Defaults produce a
    deterministic vector per input so tests can assert on shape (e.g.
    "one vector per chunk") without needing to configure a response for
    every scenario.
    """

    def __init__(
        self,
        *,
        document_vectors: list[list[float]] | Exception | None = None,
        query_vector: list[float] | Exception | None = None,
        model_name: str = "fake-embedding-model",
        dimension: int = 8,
    ) -> None:
        self._document_vectors = document_vectors
        self._query_vector = query_vector
        self._model_name = model_name
        self._dimension = dimension
        self.embed_documents_calls: list[list[str]] = []
        self.embed_query_calls: list[str] = []

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embed_documents_calls.append(texts)
        if isinstance(self._document_vectors, Exception):
            raise self._document_vectors
        if self._document_vectors is not None:
            return self._document_vectors
        return [[0.1] * self._dimension for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        self.embed_query_calls.append(text)
        if isinstance(self._query_vector, Exception):
            raise self._query_vector
        if self._query_vector is not None:
            return self._query_vector
        return [0.1] * self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension
