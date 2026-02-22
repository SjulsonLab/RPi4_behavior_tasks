from __future__ import annotations

from typing import Callable

from runtime.session_config import SessionConfig



def run_protocol(
    session: SessionConfig,
    emit_event: Callable[[str, dict[str, object]], None],
) -> dict[str, object]:
    if session.protocol == "noop":
        from protocols.noop.runner import run_noop

        return run_noop(session=session, emit_event=emit_event)

    raise ValueError(
        f"Unsupported protocol '{session.protocol}'. "
        "Only 'noop' is implemented in Phase 0 scaffolding."
    )
