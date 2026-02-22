from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.baseline_snapshot import BaselineCase, build_seeded_snapshot


BASELINE_DIR = ROOT / "tests" / "baselines"


class SeededBaselineRegressionTest(unittest.TestCase):
    def test_seeded_baselines_match_expected_snapshots(self) -> None:
        baseline_files = sorted(BASELINE_DIR.glob("*.json"))
        self.assertTrue(baseline_files, "No baseline files found under tests/baselines.")

        for baseline_file in baseline_files:
            with self.subTest(case=baseline_file.stem):
                with baseline_file.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)

                case_name = str(payload["case"])
                protocol = str(payload["protocol"])
                parameters = payload["parameters"]
                self.assertIsInstance(parameters, dict)
                expected_snapshot = payload["snapshot"]

                case = BaselineCase(protocol=protocol, parameters=parameters)
                actual_snapshot = build_seeded_snapshot(case=case, case_name=case_name)

                self.assertEqual(expected_snapshot, actual_snapshot)


if __name__ == "__main__":
    unittest.main()
