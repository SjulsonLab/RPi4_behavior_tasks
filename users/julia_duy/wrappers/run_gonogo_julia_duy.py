#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]



def main() -> int:
    command = [
        sys.executable,
        str(REPO_ROOT / "run_task.py"),
        "--protocol",
        "gonogo",
        "--template",
        "users/julia_duy/session_templates/gonogo_julia_duy_phase4.json",
        "--mouse-info",
        "users/julia_duy/mouse_info/demo_mouse_julia_duy.json",
    ]
    command.extend(sys.argv[1:])
    return subprocess.call(command, cwd=REPO_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
