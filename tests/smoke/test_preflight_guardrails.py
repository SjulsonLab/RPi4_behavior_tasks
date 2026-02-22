from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.preflight import GitState, validate_shared_checkout_guardrails
from runtime.release_policy import ReleasePolicy


class PreflightGuardrailTest(unittest.TestCase):
    def test_clean_main_branch_passes(self) -> None:
        git_state = GitState(
            branch="main",
            commit="deadbeef",
            dirty=False,
            exact_tag=None,
        )
        violations = validate_shared_checkout_guardrails(git_state)
        self.assertEqual(violations, [])

    def test_release_tag_passes(self) -> None:
        git_state = GitState(
            branch="HEAD",
            commit="deadbeef",
            dirty=False,
            exact_tag="v1.2.0",
        )
        violations = validate_shared_checkout_guardrails(git_state)
        self.assertEqual(violations, [])

    def test_dirty_checkout_fails(self) -> None:
        git_state = GitState(
            branch="main",
            commit="deadbeef",
            dirty=True,
            exact_tag="v1.2.0",
        )
        violations = validate_shared_checkout_guardrails(git_state)
        self.assertTrue(any("dirty" in issue.lower() for issue in violations))

    def test_non_release_ref_fails(self) -> None:
        git_state = GitState(
            branch="julia_hung/debug",
            commit="deadbeef",
            dirty=False,
            exact_tag=None,
        )
        violations = validate_shared_checkout_guardrails(git_state)
        self.assertTrue(any("allowed release ref" in issue.lower() for issue in violations))

    def test_custom_policy_allows_custom_branch(self) -> None:
        policy = ReleasePolicy(
            allowed_release_branches=("production",),
            allowed_release_branch_prefixes=(),
            allowed_release_tag_prefixes=("rel-",),
            require_clean_tree_in_production=True,
        )
        git_state = GitState(
            branch="production",
            commit="deadbeef",
            dirty=False,
            exact_tag=None,
        )
        violations = validate_shared_checkout_guardrails(git_state=git_state, policy=policy)
        self.assertEqual(violations, [])

    def test_require_release_tag_blocks_untagged_head(self) -> None:
        policy = ReleasePolicy(require_release_tag_in_production=True)
        git_state = GitState(
            branch="main",
            commit="deadbeef",
            dirty=False,
            exact_tag=None,
        )
        violations = validate_shared_checkout_guardrails(git_state=git_state, policy=policy)
        self.assertTrue(any("release tag is required" in issue.lower() for issue in violations))

    def test_require_release_tag_accepts_tagged_head(self) -> None:
        policy = ReleasePolicy(require_release_tag_in_production=True)
        git_state = GitState(
            branch="HEAD",
            commit="deadbeef",
            dirty=False,
            exact_tag="v2.0.1",
        )
        violations = validate_shared_checkout_guardrails(git_state=git_state, policy=policy)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
