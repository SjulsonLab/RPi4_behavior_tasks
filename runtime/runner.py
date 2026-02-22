from __future__ import annotations

from typing import Callable

from runtime.session_config import SessionConfig


MAINTAINED_PROTOCOLS = ("noop", "gonogo", "go_nogo", "context", "matt_context")
EXPERIMENTAL_PROTOCOLS = (
    "soyoun_treadmill",
    "soyoun_treadmill_experimental",
    "ivsa",
    "cue_ivsa",
)
SUPPORTED_PROTOCOLS = MAINTAINED_PROTOCOLS

GONOGO_PROTOCOL_ALIASES = {"gonogo", "go_nogo"}
CONTEXT_PROTOCOL_ALIASES = {"context", "matt_context"}
SOYOUN_TREADMILL_ALIASES = {"soyoun_treadmill", "soyoun_treadmill_experimental"}
IVSA_ALIASES = {"ivsa", "cue_ivsa"}



def run_protocol(
    session: SessionConfig,
    emit_event: Callable[[str, dict[str, object]], None],
) -> dict[str, object]:
    if session.protocol == "noop":
        from protocols.noop.runner import run_noop

        return run_noop(session=session, emit_event=emit_event)

    if session.protocol in GONOGO_PROTOCOL_ALIASES:
        from protocols.gonogo.runner import run_gonogo

        return run_gonogo(session=session, emit_event=emit_event)

    if session.protocol in CONTEXT_PROTOCOL_ALIASES:
        from protocols.context.runner import run_context

        return run_context(session=session, emit_event=emit_event)

    if session.protocol in SOYOUN_TREADMILL_ALIASES:
        from protocols.experimental.soyoun_treadmill.runner import run_soyoun_treadmill

        return run_soyoun_treadmill(session=session, emit_event=emit_event)

    if session.protocol in IVSA_ALIASES:
        from protocols.experimental.ivsa.runner import run_ivsa

        return run_ivsa(session=session, emit_event=emit_event)

    raise ValueError(
        f"Unsupported protocol '{session.protocol}'. "
        f"Maintained protocols: {', '.join(MAINTAINED_PROTOCOLS)}. "
        f"Experimental protocols: {', '.join(EXPERIMENTAL_PROTOCOLS)}."
    )
