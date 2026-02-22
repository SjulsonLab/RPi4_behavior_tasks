from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class BehaviorEvent:
    """Single behavior event emitted by protocol runtime code."""

    event_type: str
    payload: dict[str, object]
    timestamp: str


def make_behavior_event(
    event_type: str,
    payload: dict[str, object],
    timestamp: str | None = None,
) -> BehaviorEvent:
    return BehaviorEvent(
        event_type=event_type,
        payload=payload,
        timestamp=timestamp if timestamp else datetime.now(timezone.utc).isoformat(),
    )
