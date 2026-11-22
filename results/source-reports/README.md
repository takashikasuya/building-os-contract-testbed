# Source reports

These are the original verification reports, preregistrations and the contract-suite README, imported from the private
testbed at commit `e7e020dfa9ecf1df5afbcb555b84f3f055473943` by `tools/export_reports.py`. They are written in Japanese.

What changed on import, and nothing else:

1. The approving person's handle was replaced with `human:<approver>`.
2. The private GitHub owner in repository references was replaced with `private/`.
3. Relative links to other imported files were re-pointed. Links to files that were not exported (run artifacts,
   manifest, scripts, other reports) were turned into plain text marked "not exported".

The export refuses to write if the multiset of digit sequences in a file changes, so no number was altered.
[release/export-provenance.json](../../release/export-provenance.json) records the sha256 of each original and each
published file, and the number of redactions and link changes. The tests check that the published files still match.

Paths like `artifacts/...` and `manifest.yaml` keys inside the reports refer to private records. They are not in
this repository.

| Report | Experiment |
|---|---|
| [verification/2026-11-08-b3-injection.md](verification/2026-11-08-b3-injection.md) | B3 |
| [verification/2026-11-21-b11-contract-layers.md](verification/2026-11-21-b11-contract-layers.md) | B11 |
| [verification/2026-11-21-b12-v3-validation.md](verification/2026-11-21-b12-v3-validation.md) | B12 |
| [verification/2026-11-21-b13-lifecycle-offline.md](verification/2026-11-21-b13-lifecycle-offline.md) | B13 scenarios 1/2/3/5 |
| [verification/2026-11-21-b13-s4.md](verification/2026-11-21-b13-s4.md) | B13 scenario 4 |
| [verification/2026-11-08-px4-stage1-analysis.md](verification/2026-11-08-px4-stage1-analysis.md) | PX4 stage 1 |
| [verification/2026-11-12-px4-stage2-offline.md](verification/2026-11-12-px4-stage2-offline.md) | PX4 stage 2 offline |
| [verification/2026-11-21-px4-stage2-live-b.md](verification/2026-11-21-px4-stage2-live-b.md) | PX4 stage 2 live B |
| [contract-suite/README.md](contract-suite/README.md) | B1 contract suite |
| `preregistration/` (13 files) | the preregistrations the reports cite |
