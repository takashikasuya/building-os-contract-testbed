# building-os-contract-testbed

Offline contract checks for building-automation integration experiments
(BOPTEST / hvac-sim → Nexus Gateway → Building OS RI → BDE). The repository holds:

- **contract predicates** that judge one recorded interaction trace against the contract model
  C(o) = ⟨Pre, Post, Fail, T⟩, layered V0 (structure) → V1 (identity, permission, schema) → V2 (time, readback,
  release, audit) → V3 (unit, missing-not-filled, unverifiable-refused, release-failure-reported);
- **synthetic fixtures** shaped after the reported injections, so the predicates can be exercised without any live
  system;
- **result records** of the B11, B12, B13 and PX4 experiments, imported from the original reports with their
  Pass / Fail / Skip / Not Tested status, and traceable to the report text.

It does **not** contain, require or control BOPTEST, Nexus Gateway, Building OS RI, BDE or any real equipment.

> Status: release candidate, **not yet approved for publication**. See [docs/publication-audit.md](docs/publication-audit.md).

## Quick start (offline, no network services)

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest -q tests/offline tests/contract
python -m bos_contract_testbed.suite          # structure and counts of the contract suite
python tools/release_gate.py --allow-blocked  # publication checks (allowlist, scans, approvals)
```

Python 3.10 or newer. The only runtime dependency is PyYAML.

## What is and is not reproducible here

| Reproducible from this repository | Not reproducible here |
|---|---|
| Predicate logic of S/C and V0–V3, and the B13 S4 judge, on synthetic traces | The recorded traces and run artifacts (private) |
| Contract suite structure and its status counts (35 conditions) | Any live run (B12 control injections, B13 S4, PX4 live) |
| Traceability of every published number to its report | Re-computation of the measured numbers |

See [docs/reproducibility.md](docs/reproducibility.md) and [results/summary.md](results/summary.md).

## Layout

| Path | Content |
|---|---|
| `src/bos_contract_testbed/` | predicates (`checks`, `layers`, `v3`, `lifecycle`) and the suite checker (`suite`) |
| `src/bos_contract_testbed/data/bos-contract-suite.yaml` | contract suite definition v0 |
| `fixtures/synthetic/` | hand-written traces (not recorded data) |
| `tests/contract/` | unit tests of the predicates |
| `tests/offline/` | fixture-vs-report, suite and traceability tests |
| `results/` | experiment records, a summary, and the imported source reports |
| `tools/release_gate.py` | publication gate; `tools/export_reports.py` is maintainer-only |
| `docs/` | architecture, contract model, reproducibility, limitations, audit, licensing |

## Documentation

[Architecture](docs/architecture.md) · [Contract model](docs/contract-model.md) ·
[Reproducibility](docs/reproducibility.md) · [Limitations](docs/limitations.md) ·
[Publication audit](docs/publication-audit.md) · [Licensing](docs/license-candidates.md) ·
[Security](SECURITY.md) · [Notice](NOTICE.md)

## License

| Material | License |
|---|---|
| Code: `src/bos_contract_testbed/*.py`, `tests/`, `tools/`, `.github/`, `pyproject.toml` | [Apache-2.0](LICENSE) |
| Docs, results, fixtures and data: `README.md`, `NOTICE.md`, `SECURITY.md`, `CHANGELOG.md`, `docs/`, `results/` (including the imported reports), `fixtures/`, `src/bos_contract_testbed/data/bos-contract-suite.yaml` | [CC-BY-4.0](LICENSES/CC-BY-4.0.txt) |

Third-party names and cited test identifiers are not covered by these licenses (see [NOTICE.md](NOTICE.md)).

---

## 概要（日本語）

ビル設備の統合実験（BOPTEST／hvac-sim → Nexus Gateway → Building OS RI → BDE）の契約を、記録された 1 本の
やり取り（trace）について判定する述語と、合成 fixture、実験結果の記録を公開するためのリポジトリです。
製品コード、実設備への制御、実認証情報は含みません。

- 再現できるのは、述語の論理（合成 trace による）、契約試験一式の構造と件数、結果の数値が元の報告書の本文に
  あることの照合です。
- 実測の数値の再計算や live の実験（B12 の制御注入、B13 シナリオ 4、PX4 の live）は、この repo だけでは再現できません。
- 結果は Pass / Fail / Skip / Not Tested を区別し、元の報告書（`results/source-reports/`、日本語、匿名化のみで
  数値は不変）から引用しています。
- ライセンス：コードは Apache-2.0、文書・結果・fixture・契約試験一式の YAML は CC-BY-4.0 です。
- 公開前のチェックは `tools/release_gate.py` で行います。人の承認は `release/approvals.yaml` に記録します。
