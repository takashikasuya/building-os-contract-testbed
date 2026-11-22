import math

from bos_contract_testbed import v3
from tests.contract.test_checks import CLOCK, control, row, telemetry
# The original's git-history test (preregistration committed before v3.py) is not ported: history is not exported.
# That ordering is recorded in results/source-reports/verification/2026-11-21-b12-v3-validation.md.


def tel(rows, sent, units=None):
    trace = telemetry(rows, sent)
    trace["units"] = units or {"P1": "K"}
    return trace


def frame(value=295.15, at="2026-10-24T00:00:00Z", accepted=True, missing=None):
    return {"point_id": "P1", "timestamp": at, "value": value, "attributes": CLOCK, "accepted": accepted, "missing": missing}


def test_a_value_in_another_temperature_unit_is_flagged_on_a_kelvin_point():
    for value in (71.6, 295150.0, 531.27):
        flags = v3.v3_flags(tel([row(value=value)], [frame(value)]))
        assert {f["condition"] for f in flags} == {"post-unit"}  # the row is read by latest and history
    assert v3.v3_flags(tel([row(value=295.15)], [frame()])) == []


def test_units_without_a_preregistered_range_are_not_judged():
    assert v3.unit_problem(1e9, "rad") is None
    assert v3.unit_problem(150.0, "degC") is not None


def test_a_missing_value_must_neither_be_filled_nor_dropped():
    filled = v3.v3_flags(tel([row(value=0.0)], [frame(None, missing="NaN")]))
    assert any(f["condition"] == "fail-missing-not-filled" and "filled" in f["reason"] for f in filled)
    assert any(f["condition"] == "post-unit" for f in filled)  # 0.0 K is also outside the K range
    dropped = v3.v3_flags(tel([], [frame(None, missing="Infinity")]))
    assert dropped and "dropped" in dropped[0]["reason"]
    rejected = v3.v3_flags(tel([], [frame(None, accepted=False, missing="null")]))
    assert rejected and "rejected" in rejected[0]["reason"]
    kept_missing = v3.v3_flags(tel([row(value=None)], [frame(None, missing="null")]))
    assert kept_missing == []  # correct handling raises no flag (B2 counting: undetected)


def test_previous_value_fill_after_a_valid_frame_is_flagged():
    sent = [frame(295.15), frame(None, at="2026-10-24T00:01:00Z", missing="null")]
    rows = [row(value=295.15), row(value=295.15, at="2026-10-24T00:01:00Z")]
    flags = v3.v3_flags(tel(rows, sent))
    assert {f["condition"] for f in flags} == {"fail-missing-not-filled"} and all("filled" in f["reason"] for f in flags)


def test_a_write_to_an_incomplete_schema_is_flagged_accepted_or_refused():
    accepted = control(schema_removed=["dataType"])
    assert "accepted" in v3.v3_flags(accepted)[0]["reason"]
    refused = control(schema_removed=["maxValue"], requests=[{"op": "write", "token": "writer", "value": 15.0,
                                                              "reached_ri": True, "status": 400, "body": None}])
    assert "refused" in v3.v3_flags(refused)[0]["reason"]
    assert v3.v3_flags(control()) == []


def test_a_silent_release_failure_is_flagged():
    req = [{"op": "release", "token": "writer", "value": 1, "reached_ri": True, "status": 202, "body": {"controlId": "c"}}]
    silent = control(requests=req, readback=None, audit=None,
                     release_after={"priority_array": [None] * 7 + [15.0] + [None] * 8, "present_value": 15.0, "relinquish_default": 12.0})
    assert [f["condition"] for f in v3.v3_flags(silent)] == ["fail-release-failure-reported"]
    ok = control(requests=req, readback=None, audit=None,
                 release_after={"priority_array": [None] * 16, "present_value": 12.0, "relinquish_default": 12.0})
    assert v3.v3_flags(ok) == []


def test_judge_counts_v3_on_top_of_v0_v2():
    verdict = v3.judge("U1", tel([row(value=71.6)], [frame(71.6)]))
    assert verdict["first_layer"] == "V3" and verdict["layers"]["V3"]["targeted"]
    assert not verdict["layers"]["V2"]["detected"]


def test_nan_is_not_a_unit_problem():
    assert v3.unit_problem(math.nan, "K") is None
