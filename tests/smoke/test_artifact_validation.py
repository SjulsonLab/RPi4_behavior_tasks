from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.artifact_validation import validate_run_directory
from runtime.logging_schema import RunMetadata, append_event, create_run_paths, write_result, write_run_metadata


class ArtifactValidationTest(unittest.TestCase):
    def test_valid_run_directory_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_paths = create_run_paths(Path(tmpdir), "SMOKE001_noop_20260222_000000")

            metadata = RunMetadata(
                run_id="SMOKE001_noop_20260222_000000",
                protocol="noop",
                preset="smoke",
                mouse_id="SMOKE001",
                project="smoke_tests",
                started_at="2026-02-22T00:00:00+00:00",
                git_branch="main",
                git_tag=None,
                git_commit="deadbeef",
                git_dirty=False,
                run_mode="debug",
                schema_version=1,
            )
            write_run_metadata(run_paths.metadata_path, metadata)
            append_event(run_paths.events_path, "session_start", {"protocol": "noop"}, "2026-02-22T00:00:00+00:00")
            append_event(
                run_paths.events_path,
                "session_complete",
                {"total_trials": 2, "outcome_counts": {"noop_ok": 2}},
                "2026-02-22T00:00:01+00:00",
            )
            write_result(
                run_paths.result_path,
                {
                    "protocol": "noop",
                    "preset": "smoke",
                    "total_trials": 2,
                    "outcome_counts": {"noop_ok": 2},
                    "outcomes": ["noop_ok", "noop_ok"],
                },
            )

            errors = validate_run_directory(run_paths.run_dir)
            self.assertEqual(errors, [])

    def test_result_count_mismatch_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_paths = create_run_paths(Path(tmpdir), "SMOKE001_noop_20260222_000001")

            metadata = RunMetadata(
                run_id="SMOKE001_noop_20260222_000001",
                protocol="noop",
                preset="smoke",
                mouse_id="SMOKE001",
                project="smoke_tests",
                started_at="2026-02-22T00:00:00+00:00",
                git_branch="main",
                git_tag=None,
                git_commit="deadbeef",
                git_dirty=False,
                run_mode="debug",
                schema_version=1,
            )
            write_run_metadata(run_paths.metadata_path, metadata)
            append_event(run_paths.events_path, "session_start", {"protocol": "noop"}, "2026-02-22T00:00:00+00:00")
            write_result(
                run_paths.result_path,
                {
                    "protocol": "noop",
                    "preset": "smoke",
                    "total_trials": 3,
                    "outcome_counts": {"noop_ok": 2},
                    "outcomes": ["noop_ok", "noop_ok"],
                },
            )

            errors = validate_run_directory(run_paths.run_dir)
            self.assertTrue(any("total_trials" in issue for issue in errors))


if __name__ == "__main__":
    unittest.main()
