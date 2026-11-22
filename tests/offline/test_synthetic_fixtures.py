"""The ported predicates, applied to hand-written traces, give the first detecting layer the reports record.

This checks the predicate logic against the reported per-injection outcome. It does not reproduce a measured number:
the recorded traces are not public (docs/reproducibility.md). Cases with ``mechanism: assumed`` model an observation
the public report does not describe; they are counted separately and never presented as recorded behaviour.
"""
import json
from pathlib import Path

import pytest

from bos_contract_testbed import layers, lifecycle, v3

ROOT = Path(__file__).resolve().parents[2]
B11 = json.loads((ROOT / "fixtures/synthetic/b11-injections.json").read_text())
B12 = json.loads((ROOT / "fixtures/synthetic/b12-injections.json").read_text())
S4 = json.loads((ROOT / "fixtures/synthetic/b13-s4.json").read_text())


def test_fixtures_declare_themselves_synthetic():
    for doc in (B11, B12, S4):
        assert doc["synthetic"] is True
        assert "not the recorded" in doc["note"].lower()
        assert (ROOT / doc["reported_in"]).is_file()


@pytest.mark.parametrize("injection", sorted(B11["cases"]))
def test_b11_first_layer_matches_the_report(injection):
    case = B11["cases"][injection]
    verdict = layers.judge_layers(injection, case["trace"])
    assert verdict["status"] == "Tested"
    assert verdict["first_layer"] == case["reported_first_layer"]


def test_b11_per_layer_sets_equal_the_preregistered_and_reported_sets():
    detected = {l: sorted(k for k, c in B11["cases"].items() if layers.judge_layers(k, c["trace"])["layers"][l]["detected"])
                for l in layers.LAYERS}
    assert detected == layers.EXPECTED
    assert [len(detected[l]) for l in layers.LAYERS] == [6, 7, 10]  # report: V0 6, V1 7, V2 10


@pytest.mark.parametrize("injection", sorted(B12["cases"]))
def test_b12_first_layer_matches_the_report(injection):
    case = B12["cases"][injection]
    verdict = v3.judge(injection, case["trace"])
    assert verdict["status"] == "Tested"
    assert verdict["first_layer"] == case["reported_first_layer"]


def test_b12_layer_counts_equal_the_report():
    counts = {l: sum(v3.judge(k, c["trace"])["layers"][l]["detected"] for k, c in B12["cases"].items()) for l in v3.LAYERS}
    # report: Tested 11; V3 detects 10 (all but R2); V0 0, V1 2 (M1, M2), V2 3 (M1, M2, R1)
    assert len(B12["cases"]) == 11
    assert counts == {"V0": 0, "V1": 2, "V2": 3, "V3": 10}


def test_assumed_mechanisms_are_listed_explicitly():
    assumed = sorted(k for doc in (B11, B12) for k, c in doc["cases"].items() if c["mechanism"] == "assumed")
    assert assumed == ["M1", "M2", "M3"]


@pytest.mark.parametrize("run", sorted(S4["runs"]))
def test_b13_s4_expectations_match_the_report(run, tmp_path):
    spec = S4["runs"][run]
    reads = {}
    for name in ("before", "after", "end"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(spec[name]))
        reads[name] = lifecycle.read_priority(path)
    verdict = lifecycle.judge(reads["before"], reads["after"], reads["end"], S4["p16_value"], S4["bde_last"])
    assert verdict == spec["reported"]
    assert lifecycle.scenario(verdict).startswith(spec["reported_scenario"])
