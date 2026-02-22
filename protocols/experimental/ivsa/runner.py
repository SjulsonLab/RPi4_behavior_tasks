from __future__ import annotations

from typing import Callable

from protocols.experimental.ivsa.model import IVSAProtocol, trial_record_to_dict
from runtime.events import BehaviorEvent, make_behavior_event
from runtime.session_config import SessionConfig


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def run_ivsa(
    session: SessionConfig,
    emit_event: Callable[[BehaviorEvent], None],
) -> dict[str, object]:
    emit_event(
        make_behavior_event(
            "session_start",
            {
                "protocol": session.protocol,
                "preset": session.preset,
                "mouse_id": session.mouse_info.mouse_id,
                "project": session.mouse_info.project,
            },
        )
    )

    protocol = IVSAProtocol(session)
    result = protocol.run(emit_event=emit_event)

    active_trials = sum(1 for record in protocol.trial_records if record.lever_type == "active")
    inactive_trials = sum(1 for record in protocol.trial_records if record.lever_type == "inactive")

    active_presses = sum(
        1
        for record in protocol.trial_records
        if record.lever_type == "active" and record.press_detected
    )
    inactive_presses = sum(
        1
        for record in protocol.trial_records
        if record.lever_type == "inactive" and record.press_detected
    )
    infusion_count = sum(1 for record in protocol.trial_records if record.infusion_delivered)

    summary = {
        "active_trial_count": active_trials,
        "inactive_trial_count": inactive_trials,
        "active_press_rate": _safe_rate(active_presses, active_trials),
        "inactive_press_rate": _safe_rate(inactive_presses, inactive_trials),
        "infusion_rate_on_active_presses": _safe_rate(infusion_count, active_presses),
        "infusion_count": infusion_count,
    }

    emit_event(make_behavior_event("session_summary", summary))

    return {
        "protocol": result.protocol,
        "preset": result.preset,
        "total_trials": result.total_trials,
        "outcome_counts": result.outcome_counts,
        "outcomes": result.outcomes,
        "summary": summary,
        "trial_records": [trial_record_to_dict(record) for record in protocol.trial_records],
        "infusion_count": infusion_count,
    }
