# Synthetic fixtures

All files here are **hand-written**. They contain no recorded data from any system and reproduce no measured number.
Each case imitates an observation that a report describes, so that the predicates can be exercised offline.

| File | Cases | Judged with | Reported in |
|---|---|---|---|
| `synthetic/b11-injections.json` | T1–T12 (13) | `layers.judge_layers` | B3 and B11 reports |
| `synthetic/b12-injections.json` | U1–U3, M1–M3, S1–S3, R1, R2 (11) | `v3.judge` | B12 report |
| `synthetic/b13-s4.json` | run 1, retry | `lifecycle.judge` | B13 S4 report |

Each case has:

- `description`: what the injection did, as the report describes it
- `mechanism`: `documented` when the report states the observation the trace imitates (status code, value,
  priority array), or `assumed` when the report gives the outcome but not how it was observed. M1 and M2 are modeled
  as rejected frames, and M3 as a value filled from the previous frame.
- `reported_first_layer`: the first detecting layer recorded in the report (null = not detected)

Identifiers (`P1`, `GW-SYNTH`, `LAB-SP-1`, `p1-alias`) and timestamps (2026-01-01) are placeholders.
