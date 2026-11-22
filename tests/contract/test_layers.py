import re
from pathlib import Path

import pytest

from bos_contract_testbed import layers
from tests.contract.test_checks import control, row, telemetry

CHECKS = Path(__file__).resolve().parents[2] / "src/bos_contract_testbed/checks.py"


def test_every_condition_checks_py_can_raise_has_a_layer():
    raised = set(re.findall(r'flag\("([a-z0-9-]+)"', CHECKS.read_text()))
    assert raised and raised == set(layers.LAYER_OF)


def test_layers_are_disjoint_and_follow_the_preregistration():
    assert not layers.V1 & layers.V2
    assert {"pre-id-space", "pre-write-permission", "fail-out-of-range-refused", "t-invalid-release-value",
            "t-schema-missing"} == layers.V1


def test_an_unknown_condition_stops_the_analysis():
    with pytest.raises(layers.UnknownCondition):
        layers.layer_of("not-a-condition")


def test_a_structural_rejection_is_detected_from_v0_on():
    trace = control(requests=[{"op": "write", "token": "reader", "value": 24.0, "reached_ri": True, "status": 403, "body": None}],
                    readback=None, audit=None)
    verdict = layers.judge_layers("T7", trace)
    assert verdict["first_layer"] == "V0"
    assert all(verdict["layers"][l]["detected"] for l in layers.LAYERS)
    assert verdict["layers"]["V0"]["conditions"] == ["S"]
    assert "pre-write-permission" in verdict["layers"]["V1"]["conditions"]


def test_missing_clock_metadata_is_first_detected_at_v2():
    verdict = layers.judge_layers("T4", telemetry([row(data={"gatewayId": "GW"})]))
    assert verdict["first_layer"] == "V2"
    assert not verdict["layers"]["V1"]["detected"] and verdict["layers"]["V2"]["targeted"]


def test_a_readback_mismatch_is_first_detected_at_v2():
    verdict = layers.judge_layers("T10", control(readback={"expected": 16.5, "observed": [16.0]}))
    assert verdict["first_layer"] == "V2"
    assert verdict["layers"]["V2"]["conditions"] == ["post-readback"]


def test_a_silent_injection_is_detected_by_no_layer():
    verdict = layers.judge_layers("T1", telemetry([row()]))
    assert verdict["first_layer"] is None


def test_a_safety_refusal_stays_not_tested():
    trace = control(requests=[{"op": "write", "token": "writer", "value": 24.0, "reached_ri": False, "status": 0, "body": None}])
    assert layers.judge_layers("T6", trace)["status"] == "Not Tested"
