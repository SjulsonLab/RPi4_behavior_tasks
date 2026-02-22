#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.baseline_snapshot import BASELINE_CASES, render_case_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic seeded baseline snapshot files.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tests/baselines"),
        help="Output directory for baseline JSON snapshots.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.resolve() if args.output_dir.is_absolute() else (REPO_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for case_name, case in sorted(BASELINE_CASES.items()):
        payload = render_case_payload(case_name=case_name, case=case)
        target = output_dir / f"{case_name}.json"
        with target.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        print(f"Wrote {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
