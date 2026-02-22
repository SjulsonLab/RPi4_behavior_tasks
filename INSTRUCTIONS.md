# INSTRUCTIONS.md

This file is for protocol users testing tasks on the new framework.

## What Changed
- Task runtime now uses a structured event object internally (`BehaviorEvent`) with wall-clock timestamps.
- Log output format is still `events.jsonl` with `timestamp`, `event_type`, and `payload`.
- User/project config should live under `users/<your_namespace>/`.

## What You Need To Do
1. Update your checkout.
2. Work on your own branch.
3. Use your namespace files under `users/<your_namespace>/`.
4. Run your task through `run_task.py` or your wrapper.
5. Check outputs in `.task_runs/<run_id>/`.
6. Report bugs with run artifacts attached (`run_metadata.json`, `events.jsonl`, `result.json`, `quality_report.json`).

## Recommended Workflow
1. `cd /Users/lukesjulson/codex/RPi4_refactor/targets/RPi4_behavior_tasks`
2. `git checkout main`
3. `git pull origin main`
4. `git checkout -b <your_name>/task-test-YYYYMMDD`
5. Edit `users/<your_namespace>/mouse_info/<mouse>.json`.
6. Edit `users/<your_namespace>/session_templates/<template>.json`.
7. Run task.
8. Validate output and behavior.

## Example (Julia/Duy Go/No-Go)
```bash
cd /Users/lukesjulson/codex/RPi4_refactor/targets/RPi4_behavior_tasks
git checkout main
git pull origin main
git checkout -b julia_duy/test-gonogo-20260222

python users/julia_duy/wrappers/run_gonogo_julia_duy.py \
  --yes \
  --output-dir .task_runs \
  --set trial_count=20 \
  --set seed=123
```

After the run:
1. Find the run id printed in terminal output.
2. Inspect `.task_runs/<run_id>/events.jsonl`.
3. Confirm event records have wall-clock timestamps and expected event sequence.
4. If needed, run: `python tools/verify_run_artifacts.py .task_runs/<run_id>`.

## Example (Matt Context)
```bash
cd /Users/lukesjulson/codex/RPi4_refactor/targets/RPi4_behavior_tasks
python users/matt_context/wrappers/run_context_matt.py \
  --yes \
  --output-dir .task_runs \
  --set trial_count=30 \
  --set seed=456
```

## Notes
- Experimental protocols are blocked unless you pass `--allow-experimental`.
- Production mode is stricter: use `--run-mode production`.
- Optional stricter lock for production: `--require-release-tag`.
- Do not commit per-session outputs from `.task_runs/`.
