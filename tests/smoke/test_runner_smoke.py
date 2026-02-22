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


if __name__ == "__main__":
    unittest.main()
