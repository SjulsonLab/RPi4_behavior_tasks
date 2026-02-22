# Go/No-Go Protocol

Consolidated shared go/no-go protocol implementation.

## Current status
Phase 1 baseline is implemented as a deterministic simulation-first model for parity
and distribution validation.

### Implemented files
- `model.py`: unified trial engine and outcome logic.
- `runner.py`: session summary and result shaping.
- `presets/default.json`: shared baseline parameters.

## Outcome rules
- `go + response` => `hit`
- `go + no response` => `miss`
- `nogo + response` => `fa`
- `nogo + no response` => `cr`

## Notes
- This implementation does not yet drive hardware signals directly.
- The current focus is parity scaffolding and consolidation.
- Hardware event integration can be added without changing output schema.
