# Changes And Task Editing Tutorial

This document summarizes the key framework changes and shows how users should edit tasks in the new repo layout.

## What Changed

## 1) Repository split and ownership model
- Hardware/runtime box control moved to `RPi4_behavior_boxes_hardware`.
- Behavioral task logic lives in `RPi4_behavior_tasks`.
- User/project-specific files are organized under `users/<namespace>/`.

Why this matters:
- Users can keep their own templates/wrappers without editing shared core files for routine parameter changes.

## 2) Shared task runtime and protocol structure
- Shared protocol engines live under `protocols/`.
- Shared execution/runtime code lives under `runtime/`.
- Main entrypoint is `run_task.py`.

Why this matters:
- One consistent way to run tasks and validate outputs across go/no-go, context, and experimental paths.

## 3) Event model update (wall-clock event objects)
- Protocol/runtime now emit structured `BehaviorEvent` objects (not raw `(event_type, payload)` tuples).
- Event object contains:
- `event_type`
- `payload`
- `timestamp` (wall-clock ISO-8601 UTC)
- File: `runtime/events.py`

Compatibility note:
- `events.jsonl` output format remains unchanged:
- `timestamp`, `event_type`, `payload`
- Existing analysis scripts reading `events.jsonl` should keep working.

## 4) Guardrails and validation
- Experimental protocols require `--allow-experimental`.
- Production mode applies stricter preflight checks: `--run-mode production`.
- Optional strict release lock: `--require-release-tag`.
- Artifact validation and quality checks run after task execution.

## 5) Current active protocol usage
- Julia and Duy: go/no-go (`gonogo`)
- Matt: context (`context`)
- Soyoun treadmill + IVSA: staged as experimental

## Brief Tutorial: Edit Your Own Task

## A) Most common case: edit parameters only
1. Create/update your namespace files:
- `users/<your_namespace>/mouse_info/<mouse>.json`
- `users/<your_namespace>/session_templates/<template>.json`
2. Run using `run_task.py` or your wrapper.
3. Inspect output in `.task_runs/<run_id>/`.

Example:
```bash
cd /Users/lukesjulson/codex/RPi4_refactor/targets/RPi4_behavior_tasks
git checkout -b yourname/update-task-params-20260222

python run_task.py \
  --protocol gonogo \
  --template users/julia_duy/session_templates/gonogo_julia_duy_phase4.json \
  --mouse-info users/julia_duy/mouse_info/demo_mouse_julia_duy.json \
  --yes \
  --output-dir .task_runs \
  --set trial_count=40 \
  --set seed=123
```

## B) Add your own wrapper (recommended)
1. Copy an existing wrapper:
- `users/julia_duy/wrappers/run_gonogo_julia_duy.py`
2. Change default `--template` and `--mouse-info` paths to your namespace.
3. Run wrapper with extra `--set` overrides as needed.

Example:
```bash
python users/matt_context/wrappers/run_context_matt.py \
  --yes \
  --output-dir .task_runs \
  --set trial_count=30 \
  --set seed=456
```

## C) Add a brand-new protocol (core development)
1. Implement protocol model under `protocols/<new_protocol>/model.py`.
2. Implement runner under `protocols/<new_protocol>/runner.py`.
3. Register protocol alias/dispatch in `runtime/runner.py`.
4. Add session template(s) under `users/shared/session_templates/` or your namespace.
5. Add smoke/parity tests under `tests/`.
6. Run `pytest -q tests`.

Important:
- New runtime protocol code should emit `BehaviorEvent` objects via `make_behavior_event(...)`.

## After You Run
Check these files for each run:
- `.task_runs/<run_id>/run_metadata.json`
- `.task_runs/<run_id>/events.jsonl`
- `.task_runs/<run_id>/result.json`
- `.task_runs/<run_id>/quality_report.json`

Optional validation:
```bash
python tools/verify_run_artifacts.py .task_runs/<run_id>
```
