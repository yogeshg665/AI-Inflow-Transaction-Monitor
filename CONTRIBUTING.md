# Contributing

Thank you for improving the AI Inflow Transaction Monitor. This pack pairs Agent
Skills with a deterministic Python engine, so changes usually touch both.

## Ground rules

- Scoring and decisions must stay deterministic. A language model may enrich the
  narrative only.
- Use pseudonymous account and counterparty identifiers and tokenized
  instruments only. Never add raw customer or banking-instrument data.
- Keep thresholds in `config/config.yaml`; do not hardcode them.

## Adding or changing a detector

1. Implement the detector under `src/inflow_monitor/skills/` as a `Skill`
   subclass that emits at most one `RiskSignal` with a clear rationale.
2. Register it in `src/inflow_monitor/skills/registry.py` and give it a weight in
   `config/config.yaml`.
3. Document it with a `SKILL.md` under `skills/<name>/` using `template/SKILL.md`.
4. Add tests under `tests/`.

## Checks

Run all of these before opening a pull request:

```bash
python scripts/validate_skills.py
python -m ruff check src/inflow_monitor tests
python -m mypy src/inflow_monitor
python -m pytest -q
```
