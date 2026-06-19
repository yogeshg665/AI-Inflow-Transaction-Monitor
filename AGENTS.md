# AGENTS.md

Operating guide for AI agents working in this repository. This file defines how
to discover, invoke, and extend the AI Inflow Transaction Monitor skills.

## What This Repository Provides

A pack of Agent Skills that monitor inbound transactions and flag suspicious
inflows, plus a deterministic Python engine that implements the same logic and
serves as the executable reference for every skill.

- `skills/` contains one folder per skill, each with a `SKILL.md`.
- `agents/` contains specialist personas.
- `references/` contains supporting typologies, rubrics, and checklists.
- `src/inflow_monitor/` is the executable engine the skills describe.

## How to Start

1. Read `skills/using-inflow-monitor/SKILL.md`. It is the meta-skill that routes
   a request to the correct workflow and defines the shared rules.
2. Run the lifecycle in order: intake, enrichment, detection, scoring,
   decisioning, reporting.

## Operating Rules

1. Flags must be explainable and cite their signals.
2. Scoring and decisions must be deterministic. A language model may enrich the
   narrative only; it must never change the score or the decision.
3. Use pseudonymous account and counterparty identifiers. Never request or store
   raw customer or banking-instrument data.
4. Flags and reviews require human-review provisions before any customer impact.
5. Collective memory is optional and off by default. When enabled, recall and
   feedback remain deterministic, the memory signal is never critical, and
   threshold calibration is advisory only. See
   `references/memory-and-learning.md`.

## Architecture

The engine runs as a small agent swarm coordinated by an orchestrator:

- Intake and enrichment agents build the case.
- A detection swarm runs every detector independently and isolates failures.
- A scoring agent blends signals into one deterministic score.
- A decision agent applies the policy; a reporting agent emits the audit trail.

## Running the Engine

```bash
python -m pip install -e ".[dev]"
inflow-monitor monitor data/samples/sample_inflows.json --output output
pytest -q
python scripts/validate_skills.py
```

## Adding a Skill

1. Copy `template/SKILL.md` into a new folder under `skills/`.
2. Set `name` to match the folder and write a complete `description` with trigger
   phrases.
3. Fill in Overview, When to Use, Process, and Verification at minimum.
4. If the skill is executable, add the implementation under
   `src/inflow_monitor/skills/` and register it in `registry.py`.
5. Run `python scripts/validate_skills.py` and `pytest -q`.

## Conventions

- Skill folder names are lowercase with hyphens and match the `name` field.
- Each detector emits at most one risk signal with a severity, confidence, and
  rationale.
- Configuration lives in `config/config.yaml`; do not hardcode thresholds.
