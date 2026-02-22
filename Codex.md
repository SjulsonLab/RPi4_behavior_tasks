# Codex.md

Last updated: 2026-02-22
Repo: `RPi4_behavior_tasks`
Primary branch: `main`

## Purpose
Behavioral task framework split from hardware code, with shared protocol runtime, user namespaces, preflight guardrails, run artifact validation, and parity/regression tests.

## Current Architecture
- Entry point: `run_task.py`.
- Protocol implementations: `protocols/`.
- Runtime and policy layer: `runtime/`.
- User/project-owned config and wrappers: `users/`.
- Tests: `tests/` (smoke, parity, regression).

## Event Model (Current Contract)
- Protocols now emit a structured runtime event object (`BehaviorEvent`) instead of `(event_type, payload)` pairs.
- Event object definition: `runtime/events.py`.
- `BehaviorEvent` fields:
- `event_type: str`
- `payload: dict[str, object]`
- `timestamp: str` (wall-clock ISO-8601, UTC)
- Factory helper: `make_behavior_event(...)` in `runtime/events.py`.
- Dispatch signature:
- `run_protocol(..., emit_event: Callable[[BehaviorEvent], None])`
- Base protocol contract:
- `BaseProtocol.run(..., emit_event: Callable[[BehaviorEvent], None])`
- Logging path:
- `run_task.py` receives `BehaviorEvent` and writes via `append_event(...)`.
- `events.jsonl` schema is unchanged:
- `timestamp`, `event_type`, `payload`.
- Backward-compatibility:
- `runtime/logging_schema.append_event(...)` accepts either `BehaviorEvent` or legacy `event_type + payload`.

## Operator Guardrails
- `--run-mode production` enforces shared-checkout safety checks.
- `--require-release-tag` can enforce release-tag-only production runs.
- Experimental protocols require `--allow-experimental`.
- Artifact and quality validation run after each task unless explicitly disabled in debug mode.

## Important Paths
- `run_task.py`
- `runtime/events.py`
- `runtime/runner.py`
- `runtime/logging_schema.py`
- `runtime/preflight.py`
- `runtime/quality_checks.py`
- `users/julia_duy/wrappers/run_gonogo_julia_duy.py`
- `users/matt_context/wrappers/run_context_matt.py`
- `INSTRUCTIONS.md`

## Key Commands
- Run tests:
- `pytest -q tests`
- Run shared go/no-go:
- `python run_task.py --protocol gonogo --yes --output-dir .task_runs`
- Run Julia/Duy wrapper:
- `python users/julia_duy/wrappers/run_gonogo_julia_duy.py --yes --output-dir .task_runs`
- Run Matt context wrapper:
- `python users/matt_context/wrappers/run_context_matt.py --yes --output-dir .task_runs`

## Recent Changes
- Migrated runtime emit interface to structured wall-clock `BehaviorEvent` objects across all protocols, runners, and smoke/parity helpers.
- Preserved `events.jsonl` format for downstream tooling compatibility.
- Added/updated tests to validate new callback signature and keep parity/regression behavior stable.
