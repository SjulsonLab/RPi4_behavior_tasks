# RPi4_behavior_tasks (in development)

Behavioral task protocols for RPi4 behavior boxes, separated from hardware support code.

## Current status
Phase 0 scaffolding plus Phase 1/2 baselines are in place:
- Shared protocol contract and runtime modules.
- Preflight branch/commit checks.
- User/project namespace under `users/`.
- A runnable no-op protocol for smoke testing.
- Consolidated `gonogo` protocol with seeded parity/distribution tests.
- Julia/Duy go-no-go templates and wrapper entrypoint under `users/julia_duy/`.
- Consolidated `context` protocol with seeded parity/distribution tests.
- Matt context templates and wrapper entrypoint under `users/matt_context/`.

## Layout
- `protocols/`: maintained shared protocol implementations.
- `runtime/`: session config, preflight, compatibility, logging, and protocol dispatch.
- `users/`: user/project-owned metadata, templates, presets, and wrappers.
- `tests/`: smoke/parity scaffolding.

## Quickstart
Run the no-op scaffold task:

```bash
python run_task.py --protocol noop --yes --output-dir .task_runs
```

Run consolidated go/no-go with shared defaults:

```bash
python run_task.py --protocol gonogo --yes --output-dir .task_runs
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

Run tests:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```
