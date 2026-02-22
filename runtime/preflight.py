from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from runtime.release_policy import DEFAULT_RELEASE_POLICY, ReleasePolicy


@dataclass
class GitState:
    branch: str
    commit: str
    dirty: bool
    exact_tag: str | None = None



def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git_optional(repo_root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value if value else None



def get_git_state(repo_root: Path) -> GitState:
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = _git(repo_root, "rev-parse", "HEAD")
    dirty = bool(_git(repo_root, "status", "--short"))
    exact_tag = _git_optional(repo_root, "describe", "--tags", "--exact-match")
    return GitState(branch=branch, commit=commit, dirty=dirty, exact_tag=exact_tag)



def _print_preflight(protocol: str, preset: str, mouse_id: str, git_state: GitState, run_mode: str) -> None:
    print("Preflight")
    print(f"  run_mode: {run_mode}")
    print(f"  protocol: {protocol}")
    print(f"  preset: {preset}")
    print(f"  mouse_id: {mouse_id}")
    print(f"  git branch: {git_state.branch}")
    print(f"  git tag: {git_state.exact_tag}")
    print(f"  git commit: {git_state.commit}")
    print(f"  git dirty: {git_state.dirty}")



def _is_release_branch(branch: str, policy: ReleasePolicy) -> bool:
    if branch in policy.allowed_release_branches:
        return True
    return any(branch.startswith(prefix) for prefix in policy.allowed_release_branch_prefixes)



def _is_release_tag(tag: str | None, policy: ReleasePolicy) -> bool:
    if tag is None:
        return False
    return any(tag.startswith(prefix) for prefix in policy.allowed_release_tag_prefixes)



def validate_shared_checkout_guardrails(
    git_state: GitState,
    policy: ReleasePolicy = DEFAULT_RELEASE_POLICY,
) -> list[str]:
    violations: list[str] = []

    if policy.require_clean_tree_in_production and git_state.dirty:
        violations.append("Working tree is dirty. Production runs require a clean checkout.")

    if not (_is_release_branch(git_state.branch, policy) or _is_release_tag(git_state.exact_tag, policy)):
        branch_list = ", ".join(policy.allowed_release_branches)
        prefix_list = ", ".join(policy.allowed_release_branch_prefixes)
        tag_prefixes = ", ".join(policy.allowed_release_tag_prefixes)
        violations.append(
            "HEAD is not on an allowed release ref. "
            f"Allowed branches: [{branch_list}] or prefixes [{prefix_list}]. "
            f"Allowed tag prefixes: [{tag_prefixes}]."
        )

    return violations



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
    run_mode: str = "debug",
    release_policy: ReleasePolicy = DEFAULT_RELEASE_POLICY,
) -> GitState:
    if run_mode not in {"debug", "production"}:
        raise ValueError("run_mode must be one of: debug, production.")

    git_state = get_git_state(repo_root)
    _print_preflight(
        protocol=protocol,
        preset=preset,
        mouse_id=mouse_id,
        git_state=git_state,
        run_mode=run_mode,
    )

    if run_mode == "production":
        violations = validate_shared_checkout_guardrails(git_state=git_state, policy=release_policy)
        if violations:
            print("Shared-checkout guardrails: FAILED")
            for issue in violations:
                print(f"  - {issue}")
            raise RuntimeError("Preflight guardrails failed for production run.")
        print("Shared-checkout guardrails: PASS")

    if require_confirmation:
        _require_confirmation()
    return git_state
