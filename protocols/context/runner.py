from __future__ import annotations

from typing import Callable

from protocols.context.model import ContextProtocol, trial_record_to_dict
from runtime.events import BehaviorEvent, make_behavior_event
from runtime.session_config import SessionConfig



def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)



def run_context(
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

    protocol = ContextProtocol(session)
    result = protocol.run(emit_event=emit_event)

    choice_trials = sum(1 for record in protocol.trial_records if record.response_detected)
    omission_trials = sum(1 for record in protocol.trial_records if not record.response_detected)
    correct_trials = sum(1 for record in protocol.trial_records if record.correct_choice is True)
    reward_trials = sum(1 for record in protocol.trial_records if record.reward_delivered)
    switch_count = sum(1 for record in protocol.trial_records if record.switched_patch)

    left_choices = sum(1 for record in protocol.trial_records if record.choice_side == "left")
    right_choices = sum(1 for record in protocol.trial_records if record.choice_side == "right")

    summary = {
        "choice_trials": choice_trials,
        "omission_trials": omission_trials,
        "correct_choice_rate": _safe_rate(correct_trials, choice_trials),
        "reward_rate": _safe_rate(reward_trials, result.total_trials),
        "omission_rate": _safe_rate(omission_trials, result.total_trials),
        "switch_count": switch_count,
        "left_choice_count": left_choices,
        "right_choice_count": right_choices,
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
    }
