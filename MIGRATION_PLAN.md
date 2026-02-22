# RPi4 Behavior Tasks Migration Plan

## Context
This plan migrates behavioral task code out of the original monorepo into `RPi4_behavior_tasks` with **architectural cleanup first**.

Inputs agreed during planning:
- Priority: architectural cleanup over direct code copy.
- Active users/tasks to support first: Julia/Duy go-no-go, Matt context tasks.
- Soyoun treadmill task status is unknown; include later as experimental.
- Exclude `obsolete/` content from migration.
- Collapse duplicated task files into parameterized protocols + presets.
- IVSA-family tasks are currently inactive; keep as experimental (not in initial maintained set).
- Task-source precedence: runnable/sane first, newest commit date as tie-breaker.
- Runtime compatibility: keep an interactive compatibility layer during transition.
- Validation target: log parity and trial outcome parity, with seeded and distribution checks for random tasks.

## Constraints and Operating Model
### Deployment model on Pis
Current decision: one shared checkout per Pi.

Risk note:
A single shared checkout is fragile when multiple users change branches on the same machine. It can still work if branch and release controls are strict.

Required controls for this model:
1. Production runs always use a protected release tag or release branch (never a personal WIP branch).
2. User branches are only used in scheduled debugging windows.
3. Before task start, run a preflight command that prints branch/commit and requires explicit confirmation.
4. Record branch and commit hash in each session artifact.

## Branch and Source Triage
### Branch families discovered in original repo
1. Main task_protocol lineage (`main`, `charlie-irig`, `reorganization`, `luke_agent_test`) with mostly equivalent maintained task layout.
2. Headfixed extension lineage (`headfixed_soyounk`) adding headfixed variants and treadmill-related additions.
3. Go/no-go lineage (`go_nogo`, `go_nogo_temp_branch`, `benville_gonogo`, plus Julia/Duy variant in `rbb-lab`).
4. Context-heavy lineage (`context`, `context_vis`, `context_video_stim`, and broad experimental superset in `mitchfarrell-context`).
5. New model/presenter architecture lineage (`matt-behavior`) with clearer separation of model and presenter.
6. IVSA-focused lineage (`juliabenville_CueIVSA`) with active research code but currently out of immediate use.

### Selection rule
For each protocol family:
1. Prefer code that is runnable/sane (syntax-valid, coherent runtime path, no obvious breakage).
2. If multiple options remain, pick newest commit date.

## Target Repository Structure
Initial structure for `RPi4_behavior_tasks`:

```text
RPi4_behavior_tasks/
  README.md
  MIGRATION_PLAN.md
  protocols/
    gonogo/
      model.py
      runner.py
      presets/
        julia_duy_phaseX.yaml
        training_phaseX.yaml
    context/
      model.py
      presenter.py
      runner.py
      presets/
        matt_default.yaml
        matt_with_stimuli.yaml
    experimental/
      soyoun_treadmill/
      ivsa/
  runtime/
    session_config.py
    compatibility_layer.py
    preflight.py
    logging_schema.py
  tests/
    parity/
      test_gonogo_parity.py
      test_context_parity.py
    smoke/
      test_runner_smoke.py
```

## Architectural Decisions
### 1) Replace file-per-variant with protocol + preset
Current branch history has many near-duplicate task scripts. Migration will:
1. Keep one protocol implementation per task family.
2. Move behavior differences to preset configuration files.
3. Keep legacy naming as aliases during transition.

### 2) Keep a compatibility layer during transition
Support both paths initially:
1. Interactive prompts (`input`) for users who rely on current flow.
2. Config/CLI execution for reproducible runs and automation.

Planned behavior:
- If CLI/config values are present, use non-interactive mode.
- If missing, fall back to interactive prompts.

### 3) Standardize session and output metadata
Every run writes consistent metadata:
1. Task family and preset name.
2. Git branch and commit hash.
3. Random seed (if used).
4. Session start/end timestamps.

## Migration Phases
### Phase 0: Foundation
1. Create core package layout (`protocols/`, `runtime/`, `tests/`).
2. Add common runner contract and session config schema.
3. Add preflight command to print branch/commit and active preset.

Deliverable:
- Runnable skeleton with one no-op sample protocol.

### Phase 1: Go/No-Go (Julia/Duy first)
1. Select canonical go/no-go source files using runnable/sane then newest tie-breaker.
2. Implement unified go/no-go protocol.
3. Add presets for Julia/Duy operating modes.
4. Keep legacy alias runner names mapping to presets.

Validation:
1. Seeded parity test against selected reference behavior.
2. Outcome distribution checks for non-seeded runs.
3. Log schema parity against required fields.

### Phase 2: Context (Matt first)
1. Port Matt context model/presenter style into cleaned protocol package.
2. Extract context variants into presets.
3. Ensure compatibility-layer execution path remains available.

Validation:
1. Seeded trial-outcome parity where deterministic behavior is expected.
2. Distribution checks for stochastic transitions.
3. Log event parity for key state transitions and rewards.

### Phase 3: Experimental Staging
1. Add Soyoun treadmill lineage under `protocols/experimental/soyoun_treadmill`.
2. Keep excluded from default maintained set until status is confirmed.
3. Stage IVSA lineage under `protocols/experimental/ivsa` only (inactive).

Validation:
- Smoke tests only until protocol owners confirm target behavior.

### Phase 4: Hardening and Release Controls
1. Add release tags and protected release branch policy.
2. Add pre-run guardrails for shared-checkout mode.
3. Add operator runbook for branch hygiene on shared Pis.

## Parity and Test Strategy
### Deterministic parity
Use fixed seeds and fixed presets to compare:
1. Trial outcome sequence.
2. Reward/no-reward decisions.
3. Key state-transition event ordering.

### Stochastic parity
For random tasks, compare distributions over repeated runs:
1. Outcome rates (hit/miss/cr/fa) within tolerance windows.
2. Reward probability and switch behavior within tolerance windows.

### Log parity
Not byte-for-byte matching. Compare required semantic fields:
1. Session metadata fields.
2. Transition and outcome event classes.
3. Reward and punishment action records.

## Exclusions
1. `obsolete/` directory content is excluded.
2. Broken or syntax-invalid files are excluded from maintained code paths unless repaired in a dedicated experimental track.
3. IVSA is excluded from initial maintained rollout.

## Risks and Mitigations
### Risk: shared checkout branch switching disrupts runs
Mitigation:
1. Require release-tag checkout for production sessions.
2. Preflight prints branch/commit and requires operator confirmation.
3. Save branch/commit in session metadata.

### Risk: historical branch drift causes ambiguous source choice
Mitigation:
1. Use runnable/sane-first source-selection rubric.
2. Document source commit per migrated protocol and preset.

### Risk: hidden user workflow dependencies on interactive prompts
Mitigation:
1. Preserve interactive path through compatibility layer.
2. Add opt-in non-interactive mode without forcing immediate behavior change.

## Definition of Done for Initial Migration
1. Go/no-go and context families run end-to-end from `RPi4_behavior_tasks`.
2. Required parity checks pass:
   - seeded parity for deterministic checks,
   - distribution parity for stochastic checks,
   - required log-field parity.
3. `obsolete/` content excluded.
4. Soyoun treadmill and IVSA staged under experimental only.
5. Shared-checkout preflight guardrails and runbook documented.

## Immediate Next Actions
1. Implement Phase 0 skeleton in this repo.
2. Port and validate go/no-go family (Julia/Duy path first).
3. Port and validate Matt context family.
4. Stage Soyoun treadmill and IVSA as experimental tracks.
