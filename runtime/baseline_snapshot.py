from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from runtime.events import BehaviorEvent
from runtime.runner import run_protocol
from runtime.session_config import MouseInfo, SessionTemplate, build_session_config


@dataclass(frozen=True)
class BaselineCase:
    protocol: str
    parameters: dict[str, Any]


BASELINE_CASES: dict[str, BaselineCase] = {
    "noop_seeded_small": BaselineCase(
        protocol="noop",
        parameters={
            "trial_count": 6,
            "seed": 11,
        },
    ),
    "gonogo_seeded_small": BaselineCase(
        protocol="gonogo",
        parameters={
            "trial_count": 20,
            "seed": 7,
            "go_probability": 0.5,
            "response_prob_go": 0.8,
            "response_prob_nogo": 0.2,
            "lockout_length_s": 1.5,
            "response_window_s": 1.5,
            "iti_min_s": 2.0,
            "iti_max_s": 4.0,
            "enforce_timing": False,
        },
    ),
    "context_seeded_small": BaselineCase(
        protocol="context",
        parameters={
            "trial_count": 24,
            "start_patch": "right",
            "response_probability": 0.95,
            "patch_choice_accuracy": 0.75,
            "correct_reward_probability": 0.9,
            "incorrect_reward_probability": 0.0,
            "switch_probability": 0.2,
            "max_correct_trials_in_patch": 10,
            "intertrial_interval_s": 0.0,
            "seed": 17,
            "enforce_timing": False,
        },
    ),
    "soyoun_treadmill_seeded_small": BaselineCase(
        protocol="soyoun_treadmill",
        parameters={
            "trial_count": 16,
            "reward_zone_probability": 0.4,
            "lick_probability_reward_zone": 0.8,
            "lick_probability_neutral_zone": 0.2,
            "speed_mean_cm_s": 15.0,
            "speed_std_cm_s": 2.0,
            "trial_duration_s": 1.5,
            "intertrial_interval_s": 0.0,
            "seed": 31,
            "enforce_timing": False,
        },
    ),
    "ivsa_seeded_small": BaselineCase(
        protocol="ivsa",
        parameters={
            "trial_count": 18,
            "active_lever_probability": 0.5,
            "press_probability_active": 0.6,
            "press_probability_inactive": 0.1,
            "infusion_probability_given_active_press": 0.9,
            "timeout_s": 0.0,
            "seed": 53,
            "enforce_timing": False,
        },
    ),
}


def build_seeded_snapshot(case: BaselineCase, case_name: str) -> dict[str, Any]:
    template = SessionTemplate(
        protocol=case.protocol,
        preset=f"baseline_{case_name}",
        max_minutes=1,
        required_parameters=[],
        parameters={},
    )
    mouse = MouseInfo(mouse_id="BASELINE_MOUSE", project="baseline_tests")
    session = build_session_config(
        template=template,
        mouse_info=mouse,
        resolved_parameters=case.parameters,
        source_template=f"baseline:{case_name}",
    )

    events: list[BehaviorEvent] = []

    def emit_event(event: BehaviorEvent) -> None:
        events.append(event)

    result = run_protocol(session=session, emit_event=emit_event)
    event_counts = dict(sorted(Counter(event.event_type for event in events).items()))

    return {
        "protocol": result["protocol"],
        "total_trials": result["total_trials"],
        "outcome_counts": result["outcome_counts"],
        "outcomes": result["outcomes"],
        "event_type_counts": event_counts,
        "first_event_type": events[0].event_type if events else None,
        "last_event_type": events[-1].event_type if events else None,
    }


def render_case_payload(case_name: str, case: BaselineCase) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "case": case_name,
        "protocol": case.protocol,
        "parameters": case.parameters,
        "snapshot": build_seeded_snapshot(case=case, case_name=case_name),
    }
