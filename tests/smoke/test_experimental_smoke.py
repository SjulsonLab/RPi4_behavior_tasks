from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.runner import run_protocol
from runtime.events import BehaviorEvent
from runtime.session_config import MouseInfo, SessionTemplate, build_session_config


class ExperimentalRunnerSmokeTest(unittest.TestCase):
    def test_soyoun_treadmill_runner_executes(self) -> None:
        template = SessionTemplate(
            protocol="soyoun_treadmill",
            preset="smoke_soyoun_treadmill",
            max_minutes=1,
            required_parameters=[],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="SMOKE_SOYOUN_001", project="smoke_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={
                "trial_count": 10,
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
            source_template="inline",
        )

        events: list[BehaviorEvent] = []

        def emit_event(event: BehaviorEvent) -> None:
            events.append(event)

        result = run_protocol(session=session, emit_event=emit_event)

        self.assertEqual(result["protocol"], "soyoun_treadmill")
        self.assertEqual(result["total_trials"], 10)
        self.assertEqual(sum(result["outcome_counts"].values()), 10)
        self.assertIn("summary", result)
        self.assertTrue(events)
        self.assertEqual(events[0].event_type, "session_start")

    def test_ivsa_runner_executes(self) -> None:
        template = SessionTemplate(
            protocol="ivsa",
            preset="smoke_ivsa",
            max_minutes=1,
            required_parameters=[],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="SMOKE_IVSA_001", project="smoke_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={
                "trial_count": 12,
                "active_lever_probability": 0.5,
                "press_probability_active": 0.6,
                "press_probability_inactive": 0.1,
                "infusion_probability_given_active_press": 0.9,
                "timeout_s": 0.0,
                "seed": 53,
                "enforce_timing": False,
            },
            source_template="inline",
        )

        events: list[BehaviorEvent] = []

        def emit_event(event: BehaviorEvent) -> None:
            events.append(event)

        result = run_protocol(session=session, emit_event=emit_event)

        self.assertEqual(result["protocol"], "ivsa")
        self.assertEqual(result["total_trials"], 12)
        self.assertEqual(sum(result["outcome_counts"].values()), 12)
        self.assertIn("summary", result)
        self.assertTrue(events)
        self.assertEqual(events[0].event_type, "session_start")


if __name__ == "__main__":
    unittest.main()
