# RPi4_behavior_tasks (in development)

Behavioral task protocols for RPi4 behavior boxes, separated from hardware support code.

## Current status
Phase 0 scaffolding plus Phase 1/2 baselines are in place, and Phase 3
experimental staging is now wired. Phase 4/5/6 release controls are now available:
- Shared protocol contract and runtime modules.
- Preflight branch/commit checks.
- User/project namespace under `users/`.
- A runnable no-op protocol for smoke testing.
- Consolidated `gonogo` protocol with seeded parity/distribution tests.
- Julia/Duy go-no-go templates and wrapper entrypoint under `users/julia_duy/`.
- Consolidated `context` protocol with seeded parity/distribution tests.
- Matt context templates and wrapper entrypoint under `users/matt_context/`.
- Experimental Soyoun treadmill and IVSA protocol staging paths.
- Explicit `--allow-experimental` guard for experimental protocol execution.
- Production guardrails with `--run-mode production`.
- Optional strict production lock with `--require-release-tag`.
- Run metadata now records branch, tag, commit, dirty state, and run mode.
- Shared-checkout operator runbook and contributor ownership guidance.
- CI workflow runs smoke/parity tests on push and pull requests.
- Automatic run-artifact structural validation after each task run.
  - Debug-only escape hatch: `--no-validate-artifacts`

## Layout
- `protocols/`: maintained shared protocol implementations.
- `runtime/`: session config, preflight, compatibility, logging, and protocol dispatch.
- `users/`: user/project-owned metadata, templates, presets, and wrappers.
- `tests/`: smoke/parity scaffolding.
- `RUNBOOK_SHARED_CHECKOUT.md`: operator playbook for one-checkout-per-Pi operation.
- `CONTRIBUTING.md`: ownership boundaries and merge policy.

## Quickstart
Run the no-op scaffold task:

```bash
python run_task.py --protocol noop --yes --output-dir .task_runs
```

Run consolidated go/no-go with shared defaults:

```bash
python run_task.py --protocol gonogo --yes --output-dir .task_runs
```

Run consolidated go/no-go in production mode (guardrails on):

```bash
python run_task.py --protocol gonogo --run-mode production --output-dir .task_runs
```

Run production with strict tag lock (recommended for shared Pis):

```bash
python run_task.py --protocol gonogo --run-mode production --require-release-tag --output-dir .task_runs
```

Run Julia/Duy go-no-go wrapper:

```bash
python users/julia_duy/wrappers/run_gonogo_julia_duy.py --yes --output-dir .task_runs
```

Run consolidated context with shared defaults:

```bash
python run_task.py --protocol context --yes --output-dir .task_runs
```

Run Matt context wrapper:

```bash
python users/matt_context/wrappers/run_context_matt.py --yes --output-dir .task_runs
```

Run Soyoun treadmill staging protocol (experimental):

```bash
python run_task.py --protocol soyoun_treadmill --allow-experimental --yes --output-dir .task_runs
```

Run IVSA staging protocol (experimental):

```bash
python run_task.py --protocol ivsa --allow-experimental --yes --output-dir .task_runs
```

Run tests:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

Validate an existing run directory:

```bash
python tools/verify_run_artifacts.py .task_runs/<run_id>
```
