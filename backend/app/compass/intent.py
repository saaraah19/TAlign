"""
Intent Recognition.

Compass's first step on any user message: classify what's being asked
before deciding how to answer it. Kept as a separate, lightweight module
(rather than folded into compass.py) because intent classification is
swappable independently — e.g. it might start as a small/fast LLM call
and later become a fine-tuned classifier, without touching orchestration
logic downstream.

No implementation in Slice 0 — this defines the result shape that
`Compass.handle_message` (compass.py) will depend on once intent
detection is actually wired up (alongside the first real capability).
"""

from dataclasses import dataclass
from enum import StrEnum


class IntentCategory(StrEnum):
    """
    Coarse routing signal: does this need a single agent capability, or a
    multi-step deterministic workflow? Mirrors the Compass vs Workflow
    Engine split in CLAUDE.md.
    """

    AGENT_CAPABILITY = "agent_capability"
    WORKFLOW = "workflow"
    UNSUPPORTED = "unsupported"


@dataclass
class RecognizedIntent:
    category: IntentCategory
    #: Name of the target Agent capability or Workflow, resolved against
    #: the Compass Capability Registry before anything is invoked.
    target_name: str | None
    raw_message: str
    confidence: float | None = None
