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
        "context",
        "--template",
        "users/matt_context/session_templates/context_matt_default.json",
        "--mouse-info",
        "users/matt_context/mouse_info/demo_mouse_matt_context.json",
    ]
    command.extend(sys.argv[1:])
    return subprocess.call(command, cwd=REPO_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
