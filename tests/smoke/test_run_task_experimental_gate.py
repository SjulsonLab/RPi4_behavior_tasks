from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_task


class RunTaskExperimentalGateTest(unittest.TestCase):
    def test_maintained_protocol_allowed_without_flag(self) -> None:
        run_task.validate_protocol_access(protocol="gonogo", allow_experimental=False)

    def test_experimental_protocol_rejected_without_flag(self) -> None:
        with self.assertRaises(ValueError):
            run_task.validate_protocol_access(protocol="ivsa", allow_experimental=False)

    def test_experimental_protocol_allowed_with_flag(self) -> None:
        run_task.validate_protocol_access(protocol="ivsa", allow_experimental=True)

    def test_release_policy_default_is_not_tag_strict(self) -> None:
        policy = run_task.resolve_release_policy(require_release_tag=False)
        self.assertFalse(policy.require_release_tag_in_production)

    def test_release_policy_can_be_tag_strict(self) -> None:
        policy = run_task.resolve_release_policy(require_release_tag=True)
        self.assertTrue(policy.require_release_tag_in_production)


if __name__ == "__main__":
    unittest.main()
