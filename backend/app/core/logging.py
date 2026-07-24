"""
Structured logging.

We use structlog so every log line is a structured event (key=value pairs,
optionally JSON in production) rather than free-text strings. This matters
once Compass, the Workflow Engine, and agents are all emitting logs
concurrently — you need to filter by `workspace_id`, `agent`, `user_id`,
etc., not grep sentences.
"""

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure stdlib logging + structlog together.

    Call once, at application startup (see app/main.py). Every module in
    the codebase should log via:

        import structlog
        logger = structlog.get_logger(__name__)
        logger.info("candidate_scored", candidate_id=..., score=...)

    Event names are snake_case verbs/nouns (e.g. "candidate_scored"), not
    sentences — this keeps logs greppable and dashboard-friendly.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level,
    )

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    renderer: structlog.typing.Processor
    if settings.log_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level)
