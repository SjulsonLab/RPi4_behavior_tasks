from __future__ import annotations

from typing import Callable

from protocols.noop.model import NoOpProtocol
from runtime.session_config import SessionConfig



def run_noop(
    session: SessionConfig,
    emit_event: Callable[[str, dict[str, object]], None],
) -> dict[str, object]:
    emit_event(
        "session_start",
        {
            "protocol": session.protocol,
            "preset": session.preset,
            "mouse_id": session.mouse_info.mouse_id,
        },
    )

    protocol = NoOpProtocol(session)
    result = protocol.run(emit_event=emit_event)
    return {
        "protocol": result.protocol,
        "preset": result.preset,
        "total_trials": result.total_trials,
        "outcome_counts": result.outcome_counts,
        "outcomes": result.outcomes,
    }
