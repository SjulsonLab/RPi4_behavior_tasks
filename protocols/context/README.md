# Context Protocol

Consolidated shared context protocol implementation for Matt-style latent inference
workflows.

## Current status
Phase 2 baseline is implemented as simulation-first with:
- patch state (`left`/`right`),
- probabilistic responding and choice accuracy,
- probabilistic reward delivery,
- probabilistic and threshold-based patch switching,
- seeded reproducibility for parity testing.

### Implemented files
- `model.py`: context trial engine.
- `runner.py`: summary metrics and result shaping.
- `presets/default.json`: baseline parameter set.

## Notes
- This baseline does not yet drive hardware IO directly.
- It is designed to preserve stable outputs while we migrate branch variants.
