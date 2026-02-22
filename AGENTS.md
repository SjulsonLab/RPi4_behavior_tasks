# AGENTS.md

## Project Memory File
- This repository uses `Codex.md` in the repo root as persistent project context.
- At session start in this repo, read `Codex.md` before deeper exploration.

## `/init` Command Behavior
- If the user enters `/init` (or asks to initialize/refresh project context), create or update root `Codex.md`.
- Write `Codex.md` to the repository root: `./Codex.md`.
- Keep content concrete and current:
- Repository purpose and scope.
- Current protocol/runtime architecture.
- Event model contract and logging semantics.
- Important run/test commands and known operator workflows.
- Active branch/release status and follow-up work.

## Maintenance Rule
- When significant architecture or API changes are made, update `Codex.md` in the same session.
- If user-facing operation changes, update `INSTRUCTIONS.md` in the same session.
