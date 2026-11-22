# Reproducibility

## Run it

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest -q tests/offline tests/contract
```

No network service, container, credential or private repository is needed. CI runs the same commands on Python
3.10–3.13 ([workflow](../.github/workflows/offline-ci.yml)).

## What each test proves

| Test | Proves | Does not prove |
|---|---|---|
| `tests/contract/*` | the predicates behave as specified on hand-written traces (ported unit tests) | anything about the real systems |
| `tests/offline/test_synthetic_fixtures.py` | on look-alike traces, each injection is first detected at the layer the report records; B11 per-layer sets equal the preregistration (V0 6, V1 7, V2 10); B12 counts V0 0 / V1 2 / V2 3 / V3 10 of 11; B13 S4 E1/E2/E5 per run | that the recorded traces had these shapes. M1–M3 mechanisms are *assumed* (flagged in the fixture). |
| `tests/offline/test_contract_suite.py` | the suite definition is complete and has the published counts | that the cited test ids passed (reported as Not Tested) |
| `tests/offline/test_results_traceability.py` | every published number occurs verbatim in its imported report; statuses are strict; imported reports are byte-identical to the export | that the numbers are correct (they are the original observations, not recomputed) |

## Experiment records

[results/experiments.yaml](../results/experiments.yaml) records, for each experiment: id, contract and layer, fixture
origin, dependency commit SHAs (as stated in the reports, sometimes abbreviated), method, results with
Pass / Fail / Skip / Not Tested / Not Applicable, reproducibility class, limitations and open issues.

| Class | Meaning | Experiments |
|---|---|---|
| `offline-public` | re-runnable from this repository | B1 suite structure |
| `offline-private` | offline analysis over recorded artifacts that are not published | B11, B13 offline, PX4 stage 1, PX4 stage 2 offline |
| `live` | needs live stacks and a human approval; **not reproducible here** | B3, B12, B13 S4, PX4 stage 2 live |

Nothing was re-run for this release. The numbers are those of the original reports.

## Pinned versions

[manifest.public.yaml](../manifest.public.yaml) lists the source commit, the dependency commits each experiment
reports, and the sha256 of every published file.
