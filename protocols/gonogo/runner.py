from __future__ import annotations

from typing import Callable

from protocols.gonogo.model import GoNoGoProtocol, trial_record_to_dict
from runtime.events import BehaviorEvent, make_behavior_event
from runtime.session_config import SessionConfig



def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)



def run_gonogo(
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

    protocol = GoNoGoProtocol(session)
    result = protocol.run(emit_event=emit_event)

    go_trials = sum(1 for record in protocol.trial_records if record.trial_type == "go")
    nogo_trials = sum(1 for record in protocol.trial_records if record.trial_type == "nogo")

    hit_count = result.outcome_counts.get("hit", 0)
    miss_count = result.outcome_counts.get("miss", 0)
    fa_count = result.outcome_counts.get("fa", 0)
    cr_count = result.outcome_counts.get("cr", 0)

    summary = {
        "go_trials": go_trials,
        "nogo_trials": nogo_trials,
        "hit_rate_on_go_trials": _safe_rate(hit_count, go_trials),
        "false_alarm_rate_on_nogo_trials": _safe_rate(fa_count, nogo_trials),
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
        "reward_count": hit_count,
        "punishment_count": fa_count,
        "miss_count": miss_count,
        "correct_reject_count": cr_count,
    }
