#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.artifact_validation import validate_run_directory


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
    overall_errors = 0

    for run_dir in args.run_dirs:
        resolved = run_dir.resolve()
        errors = validate_run_directory(resolved)
        if errors:
            overall_errors += len(errors)
            print(f"[FAIL] {resolved}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[PASS] {resolved}")

    return 1 if overall_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
