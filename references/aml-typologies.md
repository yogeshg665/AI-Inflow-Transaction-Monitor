# Inbound Funds Typologies

A quick reference mapping common inbound-laundering patterns to the detectors
that surface them. Each detector emits one explainable signal; the score blends
them and the policy decides the outcome.

| Typology | Description | Detector | Signal |
| --- | --- | --- | --- |
| Structuring / smurfing | Deposits kept beneath a reporting threshold, singly or in aggregate. | `structuring` | `potential_structuring` |
| Money mule pass-through | A credit is rapidly moved out again, leaving little to rest. | `mule_activity` | `rapid_passthrough` |
| Unexpected large credit | An inbound amount far outside the account's baseline. | `credit_anomaly` | `anomalous_credit` |
| Sanctioned / high-risk source | Funds from a sanctioned, watchlisted, or high-risk origin. | `source_screening` | `high_risk_source` |
| Funnel account | A burst of inbound credits from many sources in a short window. | `inflow_velocity` | `inbound_velocity_burst` |
| Cross-border layering | Foreign-origin or currency-mismatched inflows. | `cross_border` | `cross_border_inflow` |
| Repeat adverse history | The account or counterparty has prior suspicious cases. | `prior_history` | `adverse_prior_history` |

## Notes

- Several typologies often co-occur (for example, structuring plus pass-through).
  The corroboration boost in scoring is designed to reward this overlap.
- A sanctioned-source hit is definitive: it is critical and sets a floor on the
  aggregate score so weaker signals cannot dilute it.
