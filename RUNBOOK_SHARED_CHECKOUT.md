# Shared Checkout Runbook (One Checkout per Pi)

This runbook is for the agreed deployment model: one shared repository checkout per
Raspberry Pi.

## Why this is risky
Branch switching in a shared checkout can silently change task behavior between
operators. The controls below are required to keep this mode sane.

## Controls
1. Production sessions must run with `--run-mode production`.
2. Production sessions must run from a clean checkout.
3. Production sessions must be on an allowed release ref:
`main`, `release`, `release/*`, or tags starting with `v` or `release-`.
4. Every run records branch/tag/commit/dirty state in `run_metadata.json`.
5. Recommended: enforce tag lock with `--require-release-tag`.

## Daily workflow
1. Fetch updates and tags:
```bash
git fetch --all --tags
```
2. Move to the intended release ref:
```bash
git checkout main
git pull --ff-only
```
3. Confirm clean tree before running:
```bash
git status --short
```
4. Run the task in production mode:
```bash
python run_task.py --protocol gonogo --run-mode production --output-dir .task_runs
```

5. For stricter safety on shared Pis, require release tags:
```bash
python run_task.py --protocol gonogo --run-mode production --require-release-tag --output-dir .task_runs
```

## Debug window workflow
Use this only in planned debugging windows.
1. Switch to the debug branch.
2. Run with `--run-mode debug`.
3. Do not leave the Pi on a debug branch after the window closes.
4. Return to a release ref (`main` or tagged release) before next production run.

## Failed guardrails
If production preflight fails:
1. Stop the run.
2. Resolve dirty files (commit/stash/discard intentionally).
3. Move to an allowed release branch or tag.
4. Re-run preflight in production mode.

## Artifact integrity checks
Runs are validated automatically after completion. To re-check an existing run:
```bash
python tools/verify_run_artifacts.py .task_runs/<run_id>
```
Note: production mode does not allow disabling artifact validation.
Note: production mode does not allow disabling semantic run-quality validation.

## Release cadence recommendation
1. Validate on a staging Pi in debug mode.
2. Tag the tested commit (`vX.Y.Z`).
3. Deploy by checking out the tag on production Pis.
