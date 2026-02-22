from __future__ import annotations

from typing import Callable

from protocols.experimental.soyoun_treadmill.model import SoyounTreadmillProtocol, trial_record_to_dict
from runtime.session_config import SessionConfig


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def run_soyoun_treadmill(
    session: SessionConfig,
    emit_event: Callable[[str, dict[str, object]], None],
) -> dict[str, object]:
    emit_event(
        "session_start",
        {
            "protocol": session.protocol,
            "preset": session.preset,
            "mouse_id": session.mouse_info.mouse_id,
            "project": session.mouse_info.project,
        },
    )

    protocol = SoyounTreadmillProtocol(session)
    result = protocol.run(emit_event=emit_event)

    reward_zone_trials = sum(1 for record in protocol.trial_records if record.zone == "reward_zone")
    neutral_zone_trials = sum(1 for record in protocol.trial_records if record.zone == "neutral_zone")
    reward_zone_licks = sum(
        1
        for record in protocol.trial_records
        if record.zone == "reward_zone" and record.lick_detected
    )
    neutral_zone_licks = sum(
        1
        for record in protocol.trial_records
        if record.zone == "neutral_zone" and record.lick_detected
    )
    reward_count = sum(1 for record in protocol.trial_records if record.reward_delivered)
    total_distance_cm = round(sum(record.distance_cm for record in protocol.trial_records), 4)
    mean_speed_cm_s = round(
        sum(record.speed_cm_s for record in protocol.trial_records) / result.total_trials,
        4,
    )

    summary = {
        "reward_zone_trial_count": reward_zone_trials,
        "neutral_zone_trial_count": neutral_zone_trials,
        "reward_count": reward_count,
        "reward_zone_lick_rate": _safe_rate(reward_zone_licks, reward_zone_trials),
        "neutral_zone_lick_rate": _safe_rate(neutral_zone_licks, neutral_zone_trials),
        "mean_speed_cm_s": mean_speed_cm_s,
        "total_distance_cm": total_distance_cm,
    }

    emit_event("session_summary", summary)

    return {
        "protocol": result.protocol,
        "preset": result.preset,
        "total_trials": result.total_trials,
        "outcome_counts": result.outcome_counts,
        "outcomes": result.outcomes,
        "summary": summary,
        "trial_records": [trial_record_to_dict(record) for record in protocol.trial_records],
        "reward_count": reward_count,
    }
