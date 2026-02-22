from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.runner import run_protocol
from runtime.session_config import MouseInfo, SessionTemplate, build_session_config


class SeededParityContractTest(unittest.TestCase):
    """
    Phase 0 placeholder parity contract.

    This uses the no-op scaffold to enforce the seeded reproducibility contract that
    later go/no-go and context parity tests will depend on.
    """

    def _run_with_seed(self, seed: int) -> list[str]:
        template = SessionTemplate(
            protocol="noop",
            preset="parity_contract",
            max_minutes=1,
            required_parameters=["trial_count", "seed"],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="PARITY001", project="parity_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={"trial_count": 8, "seed": seed},
            source_template="inline",
        )

        result = run_protocol(session=session, emit_event=lambda _e, _p: None)
        return list(result["outcomes"])

    def test_same_seed_produces_identical_outcomes(self) -> None:
        self.assertEqual(self._run_with_seed(123), self._run_with_seed(123))

    def test_different_seed_changes_outcomes(self) -> None:
        self.assertNotEqual(self._run_with_seed(123), self._run_with_seed(124))


if __name__ == "__main__":
    unittest.main()
