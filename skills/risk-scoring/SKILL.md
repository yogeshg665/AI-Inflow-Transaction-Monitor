---
name: risk-scoring
description: Aggregates detector signals into a single explainable risk score using a confidence-weighted, configuration-weighted blend with a corroboration boost and a critical floor. WHEN: "compute the risk score", "aggregate the signals", "combine detector outputs", "what is the overall inflow risk", "score this case".
---

# Risk Scoring

## Overview

Combines the signals produced by the detector swarm into one bounded score. The
blend rewards multiple corroborating indicators while staying robust to a single
noisy detector, and a critical hit sets a floor that cannot be diluted.

## When to Use

- After the detection swarm has produced signals and before decisioning.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `case.signals` | yes | Triggered detector signals. |
| `skill_weights` | yes | Per-detector weights from configuration. |

## Process

1. For each triggered signal, weight its severity by the detector weight and the
   signal confidence.
2. Blend into a weighted average.
3. Apply a corroboration boost that grows with the number of triggers.
4. Raise the result to the floor set by any critical signal.
5. Bound the score to 0-100.

## Outputs

A single `risk_score` on the case, in the range 0-100.

## Reference Implementation

`src/inflow_monitor/agents/risk_scoring_agent.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "Take the maximum severity instead." | A blend is more robust; the critical floor still captures definitive hits. |
| "An LLM can adjust the score." | Scoring is deterministic; models may only enrich the narrative. |

## Red Flags

- The score is not reproducible for identical inputs.
- A critical signal does not raise the score to its floor.

## Verification

- Identical inputs produce an identical score; a critical hit sets the floor.
