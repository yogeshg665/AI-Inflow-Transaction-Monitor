---
name: inflow-intake
description: Validates and normalizes a raw inbound money movement into a monitoring case with sorted account history. WHEN: "open a monitoring case", "normalize this inbound event", "validate an incoming transfer", "prepare a credit for monitoring", "intake a deposit".
---

# Inflow Intake

## Overview

Turns a raw inbound movement and its account history into a validated
`MonitoringCase`, the unit of work that flows through the rest of the pipeline.

## When to Use

- As the first stage of every monitoring request.
- Do NOT use it to score or decide; it only builds the case.

## Inputs

| Input | Required | Description |
| --- | --- | --- |
| `event` | yes | The inbound `MovementEvent` under monitoring. |
| `account_history` | no | Prior movements for the same account, any direction. |

## Process

1. Validate the event against the `MovementEvent` schema.
2. Sort account history by value date so downstream windows are well defined.
3. Construct a `MonitoringCase` with a unique case identifier.

## Outputs

A validated `MonitoringCase` with an empty enrichment map and no signals yet.

## Reference Implementation

`src/inflow_monitor/agents/intake_agent.py`.

## Rationalizations

| Excuse | Rebuttal |
| --- | --- |
| "History can stay unsorted." | Time-window detectors assume chronological order; sort it. |
| "Raw account numbers are fine here." | Only pseudonymous identifiers are permitted. |

## Red Flags

- The event fails schema validation but is processed anyway.
- Raw customer or instrument data appears in the case.

## Verification

- A `MonitoringCase` exists with a unique id and chronologically sorted history.
