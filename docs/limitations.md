# Known limitations

## Of this repository

- **Measured numbers cannot be recomputed here.** The recorded traces, run artifacts and live stacks are not
  published. The repository proves the predicate logic and the traceability of each number, not the numbers.
- **The fixtures are synthetic.** They imitate the reported observations. M1, M2 and M3 (B12) use an *assumed*
  mechanism because the public report does not describe how they were observed.
- **Ported, not complete.** The normal-input counting (B3 `normal.py`, B11 §4, B12 `normal_v3.py`), the live harnesses,
  the verify checks and the evidence lookup of the suite were not ported. They need private run records.
- **Abbreviated SHAs.** Several dependency versions appear in the reports as 7-character SHAs or truncated digests
  (`f3b93cdf…`). They are recorded as given.
- **Reports are in Japanese.** The English summary is in [results/summary.md](../results/summary.md).
- **Imported reports mention files that were not exported** (run artifacts, manifest keys, scripts). Their links
  were turned into plain text marked "not exported".

## Of the experiments (from the original reports)

- Injection sets were designed by the author. B11 is an explanatory decomposition of known B3 results, not new
  confirmatory evidence.
- Each B12 injection ran once. S1–S3 cover 3 of 7 schema-removal subsets. The telemetry injections ran RI components
  in one process, not through Nexus. R1/R2 counted only from attempt 3 (attempts 1–2 were Not Tested because of
  testbed defects).
- B12 R2 shows a release that the RI audit records as failed while it took effect on the plant. V3 does not capture
  that form.
- In B13 S4, the BACnet-visible priority array and the plant's internal array diverged after a watchdog relinquish.
  E1/E2 passed on BACnet reads, but "priority 16 takes effect on the equipment after release" was not observed
  (hvac-sim #992).
- PX4: stage 1 is exploratory and no weight met the criterion. Stage 2 offline is report-only. Stage 2 live
  questions 1–2 overall are **Not Tested** because the two plant A runs are not part of this release.
- Open product and testbed issues cited by the reports: RI #657 (cold reader does not deduplicate by id), RI #663 (a
  valueless frame is returned as 0), BDE #928 (transfer point matching), Testbed #72 (release slot check). Every
  live run used the hvac-sim plant, except PX4 plant A (BOPTEST).
