from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.runner import run_protocol
from runtime.session_config import MouseInfo, SessionTemplate, build_session_config


class ContextParityTest(unittest.TestCase):
    def _run_seeded(
        self,
        seed: int,
        trial_count: int = 120,
        response_probability: float = 0.95,
        patch_choice_accuracy: float = 0.75,
        switch_probability: float = 0.2,
        correct_reward_probability: float = 0.9,
        incorrect_reward_probability: float = 0.0,
    ) -> dict[str, object]:
        template = SessionTemplate(
            protocol="context",
            preset="parity",
            max_minutes=1,
            required_parameters=[],
            parameters={},
        )
        mouse = MouseInfo(mouse_id="PARITY_CONTEXT_001", project="parity_tests")
        session = build_session_config(
            template=template,
            mouse_info=mouse,
            resolved_parameters={
                "trial_count": trial_count,
                "start_patch": "right",
                "response_probability": response_probability,
                "patch_choice_accuracy": patch_choice_accuracy,
                "correct_reward_probability": correct_reward_probability,
                "incorrect_reward_probability": incorrect_reward_probability,
                "switch_probability": switch_probability,
                "max_correct_trials_in_patch": 999999,
                "intertrial_interval_s": 0.0,
                "seed": seed,
                "enforce_timing": False,
            },
            source_template="inline",
        )
        return run_protocol(session=session, emit_event=lambda _event: None)

    def test_same_seed_produces_identical_outcomes(self) -> None:
        result_a = self._run_seeded(seed=4321)
        result_b = self._run_seeded(seed=4321)
        self.assertEqual(result_a["outcomes"], result_b["outcomes"])
        self.assertEqual(result_a["outcome_counts"], result_b["outcome_counts"])

    def test_different_seed_changes_outcomes(self) -> None:
        result_a = self._run_seeded(seed=4321)
        result_b = self._run_seeded(seed=4322)
        self.assertNotEqual(result_a["outcomes"], result_b["outcomes"])

    def test_distribution_tracks_stationary_probabilities(self) -> None:
        # Keep switching disabled for a clean stationary expectation check.
        trial_count = 8000
        response_probability = 0.9
        patch_choice_accuracy = 0.8
        correct_reward_probability = 0.75
        incorrect_reward_probability = 0.1

        result = self._run_seeded(
            seed=101,
            trial_count=trial_count,
            response_probability=response_probability,
            patch_choice_accuracy=patch_choice_accuracy,
            switch_probability=0.0,
            correct_reward_probability=correct_reward_probability,
            incorrect_reward_probability=incorrect_reward_probability,
        )
        counts = result["outcome_counts"]

        omission_rate = counts.get("omission", 0) / trial_count
        correct_rewarded_rate = counts.get("correct_rewarded", 0) / trial_count
        correct_unrewarded_rate = counts.get("correct_unrewarded", 0) / trial_count
        incorrect_rewarded_rate = counts.get("incorrect_rewarded", 0) / trial_count
        incorrect_unrewarded_rate = counts.get("incorrect_unrewarded", 0) / trial_count

        expected_omission = 1.0 - response_probability
        expected_correct_rewarded = response_probability * patch_choice_accuracy * correct_reward_probability
        expected_correct_unrewarded = response_probability * patch_choice_accuracy * (1.0 - correct_reward_probability)
        expected_incorrect_rewarded = response_probability * (1.0 - patch_choice_accuracy) * incorrect_reward_probability
        expected_incorrect_unrewarded = response_probability * (1.0 - patch_choice_accuracy) * (1.0 - incorrect_reward_probability)

        tolerance = 0.04
        self.assertAlmostEqual(omission_rate, expected_omission, delta=tolerance)
        self.assertAlmostEqual(correct_rewarded_rate, expected_correct_rewarded, delta=tolerance)
        self.assertAlmostEqual(correct_unrewarded_rate, expected_correct_unrewarded, delta=tolerance)
        self.assertAlmostEqual(incorrect_rewarded_rate, expected_incorrect_rewarded, delta=tolerance)
        self.assertAlmostEqual(incorrect_unrewarded_rate, expected_incorrect_unrewarded, delta=tolerance)


if __name__ == "__main__":
    unittest.main()
