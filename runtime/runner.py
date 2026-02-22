from __future__ import annotations

from typing import Callable

from runtime.session_config import SessionConfig


SUPPORTED_PROTOCOLS = ("noop", "gonogo", "go_nogo", "context", "matt_context")



def run_protocol(
    session: SessionConfig,
    emit_event: Callable[[str, dict[str, object]], None],
) -> dict[str, object]:
    if session.protocol == "noop":
        from protocols.noop.runner import run_noop

        return run_noop(session=session, emit_event=emit_event)

    if session.protocol in {"gonogo", "go_nogo"}:
        from protocols.gonogo.runner import run_gonogo

        return run_gonogo(session=session, emit_event=emit_event)

    if session.protocol in {"context", "matt_context"}:
        from protocols.context.runner import run_context

        return run_context(session=session, emit_event=emit_event)

    raise ValueError(
        f"Unsupported protocol '{session.protocol}'. "
        f"Supported protocols: {', '.join(SUPPORTED_PROTOCOLS)}."
    )
