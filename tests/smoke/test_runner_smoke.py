from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.runner import run_protocol
from runtime.session_config import MouseInfo, SessionTemplate, build_session_config


class RunnerSmokeTest(unittest.TestCase):
    def test_noop_runner_executes(self) -> None:
        template = SessionTemplate(
            protocol="noop",
            preset="smoke",
            max_minutes=1,
            required_parameters=["trial_count", "seed"],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="SMOKE001", project="smoke_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={"trial_count": 4, "seed": 99},
            source_template="inline",
        )

        events: list[tuple[str, dict[str, object]]] = []

        def emit_event(event_type: str, payload: dict[str, object]) -> None:
            events.append((event_type, payload))

        result = run_protocol(session=session, emit_event=emit_event)

        self.assertEqual(result["protocol"], "noop")
        self.assertEqual(result["total_trials"], 4)
        self.assertEqual(sum(result["outcome_counts"].values()), 4)
        self.assertTrue(events)
        self.assertEqual(events[0][0], "session_start")

    def test_gonogo_runner_executes(self) -> None:
        template = SessionTemplate(
            protocol="gonogo",
            preset="smoke_gonogo",
            max_minutes=1,
            required_parameters=[],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="SMOKE_GONOGO_001", project="smoke_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={
                "trial_count": 10,
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
            source_template="inline",
        )

        events: list[tuple[str, dict[str, object]]] = []

        def emit_event(event_type: str, payload: dict[str, object]) -> None:
            events.append((event_type, payload))

        result = run_protocol(session=session, emit_event=emit_event)

        self.assertEqual(result["protocol"], "gonogo")
        self.assertEqual(result["total_trials"], 10)
        self.assertEqual(sum(result["outcome_counts"].values()), 10)
        self.assertIn("summary", result)
        self.assertTrue(events)
        self.assertEqual(events[0][0], "session_start")

    def test_context_runner_executes(self) -> None:
        template = SessionTemplate(
            protocol="context",
            preset="smoke_context",
            max_minutes=1,
            required_parameters=[],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="SMOKE_CONTEXT_001", project="smoke_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={
                "trial_count": 12,
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
            source_template="inline",
        )

        events: list[tuple[str, dict[str, object]]] = []

        def emit_event(event_type: str, payload: dict[str, object]) -> None:
            events.append((event_type, payload))

        result = run_protocol(session=session, emit_event=emit_event)

        self.assertEqual(result["protocol"], "context")
        self.assertEqual(result["total_trials"], 12)
        self.assertEqual(sum(result["outcome_counts"].values()), 12)
        self.assertIn("summary", result)
        self.assertTrue(events)
        self.assertEqual(events[0][0], "session_start")


if __name__ == "__main__":
    unittest.main()
