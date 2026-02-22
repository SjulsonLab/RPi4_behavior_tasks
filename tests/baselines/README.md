# Seeded Baselines

These JSON files are deterministic snapshots used by regression tests to detect
behavior drift.

Regenerate baselines intentionally after approved behavior changes:

```bash
python tools/generate_seeded_baselines.py --output-dir tests/baselines
```
