# Results summary

English summary of the original reports in [source-reports/](source-reports/README.md). Every number below is quoted
in [experiments.yaml](experiments.yaml) together with the report sentence it comes from, and the tests check those
quotes. Nothing was re-run for this release.

Status words: **Pass**, **Fail**, **Skip** and **Not Tested** are kept distinct. **Not Applicable** marks a measurement
or exploratory result that has no acceptance criterion. Skip and Not Tested are never counted as Pass.

| Experiment | What was asked | Result | Reproducible here? |
|---|---|---|---|
| B1 contract suite | Does every one of the 35 conditions map to a test or a gap? | Definition: covered 21 / partial 7 / gap 5 / conflict 2 (**Pass**, structural). Test-id evidence: **Not Tested** here. | structure only |
| B3 injections | Which of 13 injections are detected by S and by C? | S 6 / 13, C 10 / 13 (Not Applicable: measurement) | no (live) |
| B11 layers V0–V2 | At which layer is each B3 injection first detected? | Ran as preregistered: **Pass**. V0 6, V1 7, V2 10, equal to the preregistered expectation (**Pass**). Normal-input false positives: V1/V2 161 / 163,394 caused by a unit error in the rule; the exploratory recount gives 0 / 833. Builder SHACL: **Not Tested**. | logic on synthetic traces |
| B12 V3 | Do the four V3 conditions detect the gap/conflict injections? | 11 Tested. V3 detects 10 (all but R2), V0 0, V1 2, V2 3. V3 false positives 97 / 102,567 (0.095 %). R1/R2 attempts 1–2 **Not Tested** (testbed defects). Attempt 3: R1 detected, R2 not detected. | logic on synthetic traces (M1–M3 assumed) |
| B13 scenarios 1/2/3/5 | Lifecycle transitions observable in existing runs | Re-organisation only (Not Applicable) | no |
| B13 scenario 4 | After releasing priority 8, does priority 16 take over? | Run 1: **Not Tested** (E5 read failed, runbook defect). Retry: E1, E2, E5 **Pass** on BACnet reads. The plant-internal array diverged (not judged). | judge logic on synthetic reads |
| PX4 stage 1 | Penalty weight and transfer, offline | Exploratory: no weight met the criterion, and transfer was rejected in both directions (Not Applicable) | no |
| PX4 stage 2 offline | Method comparison, question 3 | A 25 runs, B 25 runs, all exit 0 (report-only). Questions 1–2 in this report: **Not Tested**. | no |
| PX4 stage 2 live B | Q1 Safety violations 0, Q2 agreement with offline | B in-situ and B transferred: Q1 **Pass**, Q2 **Pass** (energy relative difference 2.5e-8 / 3.3e-8, tolerance 5 %) | no (live) |
| PX4 stage 2 live A | as above, on BOPTEST | **Not Tested** in this release, so Q1–Q2 overall are **Not Tested** (2 of 4 runs) | no (live) |

Dependency versions, methods, limitations and open issues for each row are in [experiments.yaml](experiments.yaml)
and [../docs/limitations.md](../docs/limitations.md).
