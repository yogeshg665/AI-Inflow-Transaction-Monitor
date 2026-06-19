---
name: case-reporting
description: Produces an explainable, audit-ready monitoring report with an explicit reasoning trail for every fired signal, plus a deterministic narrative that an LLM may optionally refine. WHEN: "write the case report", "produce the audit trail", "summarize the monitoring decision", "explain why this was flagged", "generate the SAR-ready narrative".
---

# Case Reporting

## Overview

Assembles the final report: the event, score, decision, the full list of signals
with their evidence, an explicit one-line reasoning entry per fired signal, the
recommended actions, and a narrative. The narrative is deterministic by default
and may be refined by an LLM without changing any facts.

## When to Use

- As the final stage, after a decision is produced.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `case` | yes | The scored monitoring case with its signals. |
| `decision` | yes | The recommended outcome and actions. |

## Process

1. Build the deterministic narrative from the event, score, signals, and actions.
2. Optionally refine the narrative with the LLM; fall back to deterministic text.
3. Emit a structured report including a `reasoning` trail with one entry per
   fired signal.

## Outputs

A JSON-serializable report dictionary and the narrative attached to the decision.

## Reference Implementation

`src/inflow_monitor/agents/reporting_agent.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Let the model write the score commentary." | The model may phrase, not change, facts; numbers come from scoring. |
| "A reasoning trail is redundant with signals." | The trail is the human-readable justification auditors require. |

## Red Flags

- The report omits the reasoning trail or the recommended actions.
- The narrative introduces facts not present in the signals.

## Verification

- The report contains one reasoning entry per fired signal and an accurate
  decision and score.
