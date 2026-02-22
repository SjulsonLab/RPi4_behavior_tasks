from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.runner import run_protocol
from runtime.session_config import MouseInfo, SessionTemplate, build_session_config


class GoNoGoParityTest(unittest.TestCase):
    def _run_seeded(
        self,
        seed: int,
        trial_count: int = 80,
        go_probability: float = 0.55,
        response_prob_go: float = 0.75,
        response_prob_nogo: float = 0.2,
    ) -> dict[str, object]:
        template = SessionTemplate(
            protocol="gonogo",
            preset="parity",
            max_minutes=1,
            required_parameters=[],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="PARITY_GONOGO_001", project="parity_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={
                "trial_count": trial_count,
                "seed": seed,
                "go_probability": go_probability,
                "response_prob_go": response_prob_go,
                "response_prob_nogo": response_prob_nogo,
                "lockout_length_s": 1.5,
                "response_window_s": 1.5,
                "iti_min_s": 2.0,
                "iti_max_s": 4.0,
                "enforce_timing": False,
            },
            source_template="inline",
        )
        return run_protocol(session=session, emit_event=lambda _event, _payload: None)

    def test_same_seed_produces_identical_outcomes(self) -> None:
        result_a = self._run_seeded(seed=1234)
        result_b = self._run_seeded(seed=1234)
        self.assertEqual(result_a["outcomes"], result_b["outcomes"])
        self.assertEqual(result_a["outcome_counts"], result_b["outcome_counts"])

    def test_different_seed_changes_outcomes(self) -> None:
        result_a = self._run_seeded(seed=1234)
        result_b = self._run_seeded(seed=1235)
        self.assertNotEqual(result_a["outcomes"], result_b["outcomes"])

    def test_outcome_distribution_tracks_response_probabilities(self) -> None:
        trial_count = 5000
        go_probability = 0.6
        response_prob_go = 0.8
        response_prob_nogo = 0.2

        result = self._run_seeded(
            seed=99,
            trial_count=trial_count,
            go_probability=go_probability,
            response_prob_go=response_prob_go,
            response_prob_nogo=response_prob_nogo,
        )
        counts = result["outcome_counts"]

        hit_rate = counts.get("hit", 0) / trial_count
        miss_rate = counts.get("miss", 0) / trial_count
        fa_rate = counts.get("fa", 0) / trial_count
        cr_rate = counts.get("cr", 0) / trial_count

        expected_hit = go_probability * response_prob_go
        expected_miss = go_probability * (1.0 - response_prob_go)
        expected_fa = (1.0 - go_probability) * response_prob_nogo
        expected_cr = (1.0 - go_probability) * (1.0 - response_prob_nogo)

        tolerance = 0.04
        self.assertAlmostEqual(hit_rate, expected_hit, delta=tolerance)
        self.assertAlmostEqual(miss_rate, expected_miss, delta=tolerance)
        self.assertAlmostEqual(fa_rate, expected_fa, delta=tolerance)
        self.assertAlmostEqual(cr_rate, expected_cr, delta=tolerance)


if __name__ == "__main__":
    unittest.main()
