# Memory and Learning

The monitor ships with an optional, deterministic adaptive layer inspired by
collective-memory agent harnesses. It is disabled by default and never changes
how the score or the decision is computed.

## Capabilities

1. **Collective memory.** Completed cases are persisted to a local SQLite store
   using only pseudonymous account and counterparty identifiers.
2. **Recall (RAG-style).** Prior cases for the same account or counterparty are
   retrieved during enrichment and injected into the case. The
   `prior-history-recall` detector turns adverse history into a corroborating,
   never-critical signal.
3. **Feedback loop.** Analysts label stored cases `confirmed_suspicious` or
   `cleared`.
4. **Advisory calibration.** The `calibrate` command recommends flag and review
   thresholds from labeled cases. It is advisory only and never mutates
   configuration.

## Determinism guarantees

- Recall is an exact match on account or counterparty; no fuzzy or model-driven
  retrieval influences the score.
- The memory signal is capped and never critical, so prior history corroborates
  but never decides on its own.
- Calibration output is a recommendation; thresholds in `config/config.yaml`
  change only when a human edits them.

## Usage

```bash
# Persist and recall history during monitoring
inflow-monitor monitor data/samples/sample_inflows.json --memory .inflow_memory/memory.db

# Label a stored case, then get advisory threshold recommendations
inflow-monitor feedback <case_id> confirmed_suspicious --memory .inflow_memory/memory.db
inflow-monitor calibrate --memory .inflow_memory/memory.db
```

Enable it persistently by setting `memory.enabled: true` in `config/config.yaml`
or the `MEMORY_ENABLED` environment variable.
