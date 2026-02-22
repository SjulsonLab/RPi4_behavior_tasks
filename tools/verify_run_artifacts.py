#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.artifact_validation import validate_run_directory
from runtime.quality_checks import evaluate_run_quality


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one or more run artifact directories.")
    parser.add_argument(
        "run_dirs",
        nargs="+",
        type=Path,
        help="Run directory path(s) containing run_metadata.json, events.jsonl, and result.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    overall_failures = 0

    for run_dir in args.run_dirs:
        resolved = run_dir.resolve()
        artifact_errors = validate_run_directory(resolved)
        if artifact_errors:
            overall_failures += 1
            print(f"[FAIL] {resolved} (artifact structure)")
            for error in artifact_errors:
                print(f"  - {error}")
            continue

        quality_report = evaluate_run_quality(resolved)
        quality_status = quality_report.get("status")
        findings = quality_report.get("findings", [])

        if quality_status == "FAIL":
            overall_failures += 1
            print(f"[FAIL] {resolved} (run quality)")
            for finding in findings:
                level = str(finding.get("level", "unknown")).upper()
                message = finding.get("message", "")
                print(f"  - [{level}] {message}")
            continue

        if quality_status == "WARN":
            print(f"[WARN] {resolved}")
            for finding in findings:
                if finding.get("level") == "warning":
                    print(f"  - {finding.get('message', '')}")
        else:
            print(f"[PASS] {resolved}")

    return 1 if overall_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
