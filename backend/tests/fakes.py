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

from app.core.llm_provider import LLMMessage, LLMProvider, LLMResponse

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
