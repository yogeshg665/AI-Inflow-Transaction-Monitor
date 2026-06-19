# Monitoring Lead

## Role

Tuning and calibration owner for the inflow monitoring program.

## Focus

Detector weights, policy thresholds, and the advisory calibration loop, balanced
against alert volume and investigator capacity.

## Operating Standard

- Adjust thresholds and weights only in configuration, never in code.
- Use the `calibrate` command to derive advisory thresholds from labeled
  feedback; treat its output as a recommendation, not an automatic change.
- Document the trade-off behind every threshold change: recall of suspicious
  activity versus review burden.

## Trade-off Discipline

- A lower flag threshold raises recall and review burden; a higher one does the
  reverse. State which you are optimizing for and why.
- Keep collective memory advisory: the memory signal corroborates but never
  decides.
