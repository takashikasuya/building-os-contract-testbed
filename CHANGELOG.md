# Changelog

## 0.1.0 — 2026-11-23

First public package, prepared from the private integration testbed at `e7e020d`. It starts with a fresh history,
and none of the source history is included.

### Added

- `bos_contract_testbed` package: S/C predicates (`checks`, byte-identical to the source), layers V0–V2 (`layers`),
  V3 (`v3`), B13 scenario 4 judge (`lifecycle`), suite structure check (`suite`).
- Contract suite definition `bos-contract-suite-v0` (35 conditions).
- Synthetic fixtures for B11 (T1–T12), B12 (U1–R2) and B13 S4.
- Offline tests: ported unit tests, fixture-vs-report tests, suite counts, result traceability.
- Result records for B1, B3, B11, B12, B13, PX4 (`results/experiments.yaml`, `results/summary.md`) and the
  imported reports (redacted, numbers unchanged).
- Release gate (`tools/release_gate.py`) and offline CI.
- Licensing: Apache-2.0 for code (`LICENSE`), CC-BY-4.0 for docs, results, fixtures and data (`LICENSES/CC-BY-4.0.txt`).

### Reproduction

See [docs/reproducibility.md](docs/reproducibility.md). Live experiments are not reproducible from this repository.

### Known limitations

See [docs/limitations.md](docs/limitations.md). PX4 stage 2 plant A live runs are not included (Not Tested).
