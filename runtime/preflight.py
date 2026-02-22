from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass
class GitState:
    branch: str
    commit: str
    dirty: bool



def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()



def get_git_state(repo_root: Path) -> GitState:
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = _git(repo_root, "rev-parse", "HEAD")
    dirty = bool(_git(repo_root, "status", "--short"))
    return GitState(branch=branch, commit=commit, dirty=dirty)



def _print_preflight(protocol: str, preset: str, mouse_id: str, git_state: GitState) -> None:
    print("Preflight")
    print(f"  protocol: {protocol}")
    print(f"  preset: {preset}")
    print(f"  mouse_id: {mouse_id}")
    print(f"  git branch: {git_state.branch}")
    print(f"  git commit: {git_state.commit}")
    print(f"  git dirty: {git_state.dirty}")



def _require_confirmation() -> None:
    answer = input("Continue with this run? [y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        raise RuntimeError("Run cancelled by operator at preflight confirmation.")



def run_preflight(
    repo_root: Path,
    protocol: str,
    preset: str,
    mouse_id: str,
    require_confirmation: bool,
) -> GitState:
    git_state = get_git_state(repo_root)
    _print_preflight(protocol=protocol, preset=preset, mouse_id=mouse_id, git_state=git_state)
    if require_confirmation:
        _require_confirmation()
    return git_state
