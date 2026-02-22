# Contributing Guidelines

## Ownership boundaries
Use these boundaries to reduce merge conflicts in the shared repo:

1. Shared protocol/runtime changes belong in:
`protocols/`, `runtime/`, `tests/`, and top-level docs.
2. User/project-specific files belong in:
`users/<user_or_project>/...`
3. Shared defaults for all users belong in:
`users/shared/...`

## Branch expectations
1. Personal branches should primarily modify `users/<owner>/...`.
2. Shared core changes should be isolated and reviewed before merging.
3. Keep branch purpose narrow: one feature or migration phase per branch.

## Promotion path for user logic
If user-specific behavior becomes stable and broadly useful:
1. Add parity/smoke coverage in `tests/`.
2. Move generalized logic into `protocols/` and/or `runtime/`.
3. Keep user wrappers/templates thin and config-focused.

## Session data policy
Version in Git:
1. `mouse_info` files.
2. Session templates and presets.
3. Wrapper scripts and docs.

Do not version in Git:
1. Per-session generated files.
2. Runtime outputs (`.task_runs/`, `outputs/`, `runs/`).
3. Temporary/debug artifacts.

## Pull request checklist
1. Run tests:
```bash
python -m unittest discover -s tests -p 'test_*.py'
```
2. Ensure CI is green for the branch/PR.
3. For production-impacting changes, run one manual task in
`--run-mode production` and verify preflight/metadata fields.
4. For shared-checkout policy changes, run one manual task with
`--run-mode production --require-release-tag` when feasible.
5. Validate one produced run artifact directory:
```bash
python tools/verify_run_artifacts.py .task_runs/<run_id>
```
6. Update docs/runbook when workflow or guardrails change.
