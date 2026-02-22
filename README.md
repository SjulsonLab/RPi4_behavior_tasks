# RPi4_behavior_tasks (in development)

Behavioral task protocols for RPi4 behavior boxes, separated from hardware support code.

## Current status
Phase 0 migration scaffolding is in place:
- Shared protocol contract and runtime modules.
- Preflight branch/commit checks.
- User/project namespace under `users/`.
- A runnable no-op protocol for smoke testing.

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

Run tests:

```bash
python -m unittest discover -s tests
```
