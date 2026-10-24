"""
Shared structured-output retry helper.

Every agent that calls `LLMProvider.complete_structured` needs the same
policy: retry exactly once, and only on `InvalidStructuredOutputError`
(a schema-validation failure — a legitimate "ask the model to correct
its own formatting" case). Never retry on `LLMProviderError` (network,
timeout, rate limit) — that propagates immediately.

`ResumeIntelligenceAgent` still carries its own private inline version
of this exact logic (`_complete_structured_with_retry`), predating this
extraction — deliberately left untouched here rather than refactored,
so the existing, passing test suite for that agent has zero risk of
behavioral drift. `CommunicationAgent` is the first consumer of this
shared version. Migrating ResumeIntelligenceAgent to use this too is a
reasonable future cleanup, not done as part of this slice.
"""

from typing import TypeVar

import structlog
from pydantic import BaseModel

from app.core.exceptions import InvalidStructuredOutputError
from app.core.llm_provider import LLMMessage, LLMProvider

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


async def complete_structured_with_one_retry(
    llm: LLMProvider,
    messages: list[LLMMessage],
    schema_cls: type[T],
) -> T:
    try:
        return await llm.complete_structured(messages, response_schema=schema_cls)
    except InvalidStructuredOutputError as first_error:
        logger.warning(
            "structured_output_retry", schema=schema_cls.__name__, error=str(first_error)
        )
        retry_messages = [
            *messages,
            LLMMessage(
                role="user",
                content=(
                    "Your previous response did not match the required schema. "
                    "Respond again, strictly matching the schema and nothing else."
                ),
            ),
        ]
        try:
            return await llm.complete_structured(retry_messages, response_schema=schema_cls)
        except InvalidStructuredOutputError as second_error:
            raise InvalidStructuredOutputError(
                f"LLM did not return valid {schema_cls.__name__} output after one retry: "
                f"{second_error}"
            ) from second_error
