# Influx &middot; AI Inflow Transaction Monitor

Production-grade Agent Skills that monitor inbound transactions and flag
suspicious inflows end to end. This pack automates the first-line triage of
incoming funds: it ingests an inbound credit, enriches it with context, runs a
swarm of anti-money-laundering detectors, scores risk, recommends a disposition,
and produces an explainable, audit-ready case report with a reasoning trail for
every signal.

Each skill is a self-contained folder with a `SKILL.md` that an AI agent (Claude,
Codex, or any Agent Skills-compatible host) loads on demand. The same logic is
implemented in a deterministic Python engine that runs without any external model
or credentials, so every skill has an executable reference.

```
  INTAKE        ENRICH        DETECT         SCORE         DECIDE        REPORT
 ┌──────┐     ┌──────┐     ┌────────┐     ┌──────┐     ┌──────┐     ┌──────┐
 │ Open │ ──▶ │ Add  │ ──▶ │ Detect │ ──▶ │ Risk │ ──▶ │Policy│ ──▶ │ Case │
 │ Case │     │Context│    │ Swarm  │     │Score │     │Verdict│    │Report│
 └──────┘     └──────┘     └────────┘     └──────┘     └──────┘     └──────┘
```

## Skills

The pack includes 13 skills: 1 meta-skill that routes work, plus 12 lifecycle
skills.

### Meta

| Skill | Use When |
| --- | --- |
| [using-inflow-monitor](skills/using-inflow-monitor/SKILL.md) | Starting a monitoring request or deciding which skill applies. |

### Intake and Enrichment

| Skill | Use When |
| --- | --- |
| [inflow-intake](skills/inflow-intake/SKILL.md) | Validating and normalizing an inbound event into a case. |
| [counterparty-enrichment](skills/counterparty-enrichment/SKILL.md) | Adding baseline, counterparty, and reference context. |

### Detection

| Skill | Use When |
| --- | --- |
| [structuring-detection](skills/structuring-detection/SKILL.md) | Detecting sub-threshold and aggregated structuring. |
| [mule-activity](skills/mule-activity/SKILL.md) | Detecting rapid inbound-then-outbound pass-through. |
| [credit-anomaly](skills/credit-anomaly/SKILL.md) | Detecting inbound amounts far outside the baseline. |
| [source-screening](skills/source-screening/SKILL.md) | Screening sanctioned, watchlisted, and high-risk sources. |
| [inflow-velocity](skills/inflow-velocity/SKILL.md) | Detecting bursts of inbound credits. |
| [cross-border-risk](skills/cross-border-risk/SKILL.md) | Detecting cross-border and currency-mismatched inflows. |
| [prior-history-recall](skills/prior-history-recall/SKILL.md) | Surfacing adverse prior history from collective memory. |

### Score, Decide, Report

| Skill | Use When |
| --- | --- |
| [risk-scoring](skills/risk-scoring/SKILL.md) | Aggregating signals into a single risk score. |
| [monitoring-decisioning](skills/monitoring-decisioning/SKILL.md) | Applying the policy to clear, review, or flag. |
| [case-reporting](skills/case-reporting/SKILL.md) | Producing the audit-ready case report. |

## Agent Personas

| Persona | Role | Focus |
| --- | --- | --- |
| [aml-analyst](agents/aml-analyst.md) | AML Analyst | End-to-end monitoring with a disposition standard. |
| [monitoring-lead](agents/monitoring-lead.md) | Monitoring Lead | Threshold and weight calibration with trade-off discipline. |
| [compliance-reviewer](agents/compliance-reviewer.md) | Compliance Reviewer | Explainability, fairness, and audit controls. |

## Reference Material

| Reference | Contents |
| --- | --- |
| [aml-typologies.md](references/aml-typologies.md) | Inbound laundering patterns and the detectors that surface them. |
| [risk-scoring-rubric.md](references/risk-scoring-rubric.md) | Severity bands, confidence, and score interpretation. |
| [monitoring-policy.md](references/monitoring-policy.md) | Thresholds, outcomes, and governance. |
| [investigation-checklist.md](references/investigation-checklist.md) | Pre-close control checklist for every case. |
| [memory-and-learning.md](references/memory-and-learning.md) | Collective memory, recall, and the feedback loop. |

## Design Choices

- **Process, not prose.** Skills are workflows with steps and exit criteria.
- **Determinism first.** The score and decision are reproducible. A language
  model may enrich the narrative only.
- **Reasoning for every action.** Every flag carries a per-signal reasoning trail
  in the report.
- **Verification is non-negotiable.** Every skill ends with evidence
  requirements.

## Project Structure

```text
.
├── skills/                     13 Agent Skills (1 meta + 12 lifecycle)
├── agents/                     3 specialist personas
├── references/                 5 supplementary references
├── template/                   Skill template (SKILL.md)
├── scripts/                    Skill validator
├── src/inflow_monitor/         Deterministic Python engine (executable reference)
│   ├── agents/                 Lifecycle agents and the detection swarm
│   ├── skills/                 Inbound-monitoring detectors
│   ├── memory/                 Collective memory, recall, and feedback loop
│   ├── models/                 Pydantic domain models
│   ├── pipeline/               Batch and single-case orchestration
│   ├── llm/                    Optional LLM client and deterministic fallback
│   └── cli.py                  Command-line entry point
├── config/                     Engine configuration
├── data/samples/               Synthetic example dataset
├── tests/                      Unit and integration tests
├── plugin.json                 Skill pack manifest
├── Dockerfile                  Container image
├── docker-compose.yml          Local container orchestration
└── AGENTS.md                   Operating guide for AI agents
```

## Quick Start

### Use the Skills

Point your agent at this repository and open
[skills/using-inflow-monitor/SKILL.md](skills/using-inflow-monitor/SKILL.md). It
routes any request to the correct workflow. The folder layout follows the Agent
Skills convention, so the pack also works as a plugin manifest via `plugin.json`.

### Run the Engine

```bash
python -m pip install -e ".[dev]"
inflow-monitor monitor data/samples/sample_inflows.json --output output
```

Print a full reasoning report for the first case in a file:

```bash
inflow-monitor explain data/samples/sample_inflows.json
```

### Use the Python API

```python
from inflow_monitor.pipeline import MonitoringPipeline, load_cases_from_json

pipeline = MonitoringPipeline()
cases = load_cases_from_json("data/samples/sample_inflows.json")
results = pipeline.run_batch(cases)

for result in results:
    print(result.decision.outcome, result.decision.risk_score)
```

## Memory and Learning

The engine has an optional collective-memory and feedback loop, inspired by
adaptive-memory agent harnesses but kept fully deterministic. It is disabled by
default. See [references/memory-and-learning.md](references/memory-and-learning.md).

- **Collective memory.** Completed cases are persisted to a local SQLite store
  using only pseudonymous account and counterparty identifiers.
- **Recall.** Prior cases for the same account or counterparty are retrieved
  during enrichment; the `prior-history-recall` detector turns adverse history
  into a corroborating, non-critical signal.
- **Feedback loop.** Analysts label cases `confirmed_suspicious` or `cleared`,
  and `calibrate` recommends thresholds from those labels. Calibration is
  advisory only and never mutates configuration.

```bash
# Persist and recall history during monitoring
inflow-monitor monitor data/samples/sample_inflows.json --memory .inflow_memory/memory.db

# Label a stored case, then get advisory threshold recommendations
inflow-monitor feedback <case_id> confirmed_suspicious --memory .inflow_memory/memory.db
inflow-monitor calibrate --memory .inflow_memory/memory.db
```

## Input Format

Each input file is a JSON array of case objects. A case contains an `event`
(the inbound movement under monitoring), an optional `account_history` array of
prior movements in either direction, and an optional `enrichment` object carrying
signals from upstream reference services (for example, sanctions flags). Only
pseudonymous account and counterparty identifiers are required or stored.

```json
[
  {
    "event": {
      "event_id": "evt_1001",
      "account_id": "acct_a1",
      "counterparty_id": "cp_source",
      "direction": "inbound",
      "amount": 9600.0,
      "currency": "USD",
      "value_date": "2026-05-03T16:00:00Z",
      "channel": "cash",
      "source_country": "US",
      "account_country": "US"
    },
    "account_history": [],
    "enrichment": {}
  }
]
```

## Configuration

Engine behavior is controlled by [config/config.yaml](config/config.yaml) and
selected environment variables. Copy `.env.example` to `.env` to customize
runtime settings.

| Setting | Description |
| --- | --- |
| `decision_policy.flag_threshold` | Risk score at or above which an inflow is flagged. |
| `decision_policy.review_threshold` | Risk score at or above which a case is reviewed. |
| `skill_weights` | Relative contribution of each detector to the aggregate score. |
| `memory.enabled` | Persist cases and recall prior history. Off by default. |
| `memory.path` | SQLite path for collective memory and analyst feedback. |
| `LLM_PROVIDER` | `none`, `openai`, or `azure_openai`. Defaults to deterministic mode. |

## Containerized Execution

```bash
docker compose up --build
```

Reports are written to the host `output/` directory.

## Validation and Testing

```bash
python scripts/validate_skills.py
pytest -q
```

## Responsible Use

This system assists and accelerates inbound-transaction monitoring. Automated
flags, holds, and suspicious-activity determinations must be governed by human
oversight, customer-impact review, and the compliance controls for your
jurisdiction.

## License

Released under the MIT License. See [LICENSE](LICENSE).
