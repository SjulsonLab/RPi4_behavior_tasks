from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.logging_schema import RunMetadata, append_event, create_run_paths, write_result, write_run_metadata
from runtime.quality_checks import evaluate_run_quality


class QualityChecksTest(unittest.TestCase):
    def test_noop_quality_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_paths = create_run_paths(Path(tmpdir), "QUALITY_noop_001")
            metadata = RunMetadata(
                run_id="QUALITY_noop_001",
                protocol="noop",
                preset="smoke",
                mouse_id="Q001",
                project="quality_tests",
                started_at="2026-02-22T00:00:00+00:00",
                git_branch="main",
                git_tag=None,
                git_commit="deadbeef",
                git_dirty=False,
                run_mode="debug",
            )
            write_run_metadata(run_paths.metadata_path, metadata)
            append_event(run_paths.events_path, "session_start", {"protocol": "noop"}, "2026-02-22T00:00:00+00:00")
            append_event(
                run_paths.events_path,
                "trial",
                {"trial_index": 1, "outcome": "noop_ok"},
                "2026-02-22T00:00:01+00:00",
            )
            append_event(
                run_paths.events_path,
                "trial",
                {"trial_index": 2, "outcome": "noop_retry"},
                "2026-02-22T00:00:02+00:00",
            )
            append_event(
                run_paths.events_path,
                "session_complete",
                {"total_trials": 2},
                "2026-02-22T00:00:03+00:00",
            )
            write_result(
                run_paths.result_path,
                {
                    "protocol": "noop",
                    "preset": "smoke",
                    "total_trials": 2,
                    "outcome_counts": {"noop_ok": 1, "noop_retry": 1},
                    "outcomes": ["noop_ok", "noop_retry"],
                },
            )

            report = evaluate_run_quality(run_paths.run_dir)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["error_count"], 0)

    def test_trial_event_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_paths = create_run_paths(Path(tmpdir), "QUALITY_gonogo_001")
            metadata = RunMetadata(
                run_id="QUALITY_gonogo_001",
                protocol="gonogo",
                preset="smoke",
                mouse_id="Q002",
                project="quality_tests",
                started_at="2026-02-22T00:00:00+00:00",
                git_branch="main",
                git_tag=None,
                git_commit="deadbeef",
                git_dirty=False,
                run_mode="debug",
            )
            write_run_metadata(run_paths.metadata_path, metadata)
            append_event(run_paths.events_path, "session_start", {"protocol": "gonogo"}, "2026-02-22T00:00:00+00:00")
            append_event(
                run_paths.events_path,
                "trial_end",
                {"trial_index": 1, "outcome": "hit"},
                "2026-02-22T00:00:01+00:00",
            )
            append_event(
                run_paths.events_path,
                "session_complete",
                {"total_trials": 2},
                "2026-02-22T00:00:02+00:00",
            )
            append_event(
                run_paths.events_path,
                "session_summary",
                {"hit_rate_on_go_trials": 1.0},
                "2026-02-22T00:00:03+00:00",
            )
            write_result(
                run_paths.result_path,
                {
                    "protocol": "gonogo",
                    "preset": "smoke",
                    "total_trials": 2,
                    "outcome_counts": {"hit": 1, "miss": 1},
                    "outcomes": ["hit", "miss"],
                },
            )

            report = evaluate_run_quality(run_paths.run_dir)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(
                any(finding["check"] == "trial_event_count" for finding in report["findings"])
            )

    def test_unknown_protocol_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_paths = create_run_paths(Path(tmpdir), "QUALITY_custom_001")
            metadata = RunMetadata(
                run_id="QUALITY_custom_001",
                protocol="custom_task",
                preset="smoke",
                mouse_id="Q003",
                project="quality_tests",
                started_at="2026-02-22T00:00:00+00:00",
                git_branch="main",
                git_tag=None,
                git_commit="deadbeef",
                git_dirty=False,
                run_mode="debug",
            )
            write_run_metadata(run_paths.metadata_path, metadata)
            append_event(
                run_paths.events_path,
                "session_start",
                {"protocol": "custom_task"},
                "2026-02-22T00:00:00+00:00",
            )
            append_event(
                run_paths.events_path,
                "session_complete",
                {"total_trials": 1},
                "2026-02-22T00:00:01+00:00",
            )
            write_result(
                run_paths.result_path,
                {
                    "protocol": "custom_task",
                    "preset": "smoke",
                    "total_trials": 1,
                    "outcome_counts": {"custom": 1},
                    "outcomes": ["custom"],
                },
            )

            report = evaluate_run_quality(run_paths.run_dir)
            self.assertEqual(report["status"], "WARN")
            self.assertEqual(report["error_count"], 0)
            self.assertGreaterEqual(report["warning_count"], 1)


if __name__ == "__main__":
    unittest.main()
