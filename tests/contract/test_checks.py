import copy
import json

from bos_contract_testbed import checks

CLOCK = {"gatewayId": "GW", "sim_clock_id": "clk", "sim_config_revision": "r1", "sim_time_quality": "stable_unfenced", "sim_time_s": "3600.0"}


def row(point="P1", value=21.5, at="2026-10-24T00:00:00Z", data=CLOCK, **over):
    return {"pointId": point, "deviceId": "D1", "value": value, "datetime": at, "data": json.dumps(data), **over}


def telemetry(rows, sent=None, registered=("P1",)):
    sent = sent if sent is not None else [{"point_id": "P1", "timestamp": "2026-10-24T00:00:00Z", "value": 21.5, "attributes": CLOCK, "accepted": True}]
    return {"kind": "telemetry", "registered": list(registered), "sent": sent,
            "reads": [{"api": "latest", "point_id": "P1", "status": 200, "rows": rows[-1:]},
                      {"api": "history", "point_id": "P1", "status": 200, "rows": rows}]}


def control(**over):
    trace = {"kind": "control", "point_id": "LAB-1", "schema": {"min": 22.0, "max": 26.0}, "policy": "allow",
             "requests": [{"op": "write", "token": "writer", "value": 24.0, "reached_ri": True, "status": 202, "body": {"controlId": "c1"}}],
             "readback": {"expected": 24.0, "observed": [24.0]}, "audit": {"accepted": 1, "rows": 1}, "release_after": None}
    trace.update(over)
    return trace


def test_a_normal_telemetry_trace_is_flagged_by_neither():
    verdict = checks.judge("T1", telemetry([row()]))
    assert not verdict["S"]["detected"] and not verdict["C"]["detected"]


def test_a_unit_swap_slips_through_both():
    sent = [{"point_id": "P1", "timestamp": "2026-10-24T00:00:00Z", "value": 294.65, "attributes": CLOCK, "accepted": True}]
    verdict = checks.judge("T1", telemetry([row(value=294.65)], sent))
    assert not verdict["S"]["detected"] and not verdict["C"]["detected"]


def test_missing_clock_metadata_is_flagged_by_c_only_and_targeted():
    verdict = checks.judge("T4", telemetry([row(data={"gatewayId": "GW"})]))
    assert not verdict["S"]["detected"]
    assert verdict["C"]["detected"] and verdict["C"]["targeted"]
    assert {f["condition"] for f in verdict["C"]["flags"]} == {"post-origin-and-quality"}


def test_a_rewind_in_history_is_flagged():
    rows = [row(at="2026-10-24T00:00:00Z"), row(at="2026-10-24T00:01:00Z", data={**CLOCK, "sim_time_s": "3000.0"})]
    assert checks.rewinds(rows) and checks.judge("T5", telemetry(rows))["C"]["targeted"]


def test_changed_rows_without_sim_time_are_neither_clock_problems_nor_rewinds():
    changed = {**CLOCK, "sim_time_quality": "changed"}
    changed.pop("sim_time_s")
    rows = [row(), row(at="2026-10-24T00:01:00Z", data=changed)]
    assert checks.clock_problems(rows[1]) == [] and checks.rewinds(rows) == []


def test_an_unknown_id_is_flagged_by_c_whether_rejected_or_accepted():
    for accepted in (False, True):
        sent = [{"point_id": "p1", "timestamp": "2026-10-24T00:00:00Z", "value": 21.5, "attributes": CLOCK, "accepted": accepted}]
        verdict = checks.judge("T2b", telemetry([row()], sent))
        assert verdict["C"]["detected"] and verdict["C"]["targeted"]


def test_a_missing_envelope_field_or_non_2xx_read_is_an_s_flag():
    assert checks.judge("T3", telemetry([row(value=None)]))["S"]["detected"]
    trace = telemetry([])
    trace["reads"][0]["status"] = 404
    assert checks.judge("T2a", trace)["S"]["detected"]


def test_a_normal_control_trace_is_flagged_by_neither():
    verdict = checks.judge("T6", control())
    assert not verdict["S"]["detected"] and not verdict["C"]["detected"]


def test_out_of_range_refused_is_detected_by_both():
    trace = control(requests=[{"op": "write", "token": "writer", "value": 21.5, "reached_ri": True, "status": 400, "body": {}}], readback=None)
    verdict = checks.judge("T6", trace)
    assert verdict["S"]["detected"] and verdict["C"]["targeted"]


def test_schema_missing_under_allow_slips_through_and_under_deny_is_flagged():
    accepted = [{"op": "write", "token": "writer", "value": 24.0, "reached_ri": True, "status": 202, "body": {"controlId": "c"}}]
    allow = checks.judge("T8", control(schema=None, policy="allow", requests=accepted))
    assert not allow["S"]["detected"] and not allow["C"]["detected"]
    refused = [{"op": "write", "token": "writer", "value": 24.0, "reached_ri": True, "status": 400, "body": {}}]
    deny = checks.judge("T9", control(schema=None, policy="deny", requests=refused, readback=None))
    assert deny["S"]["detected"] and deny["C"]["targeted"]


def test_readback_difference_is_c_only():
    verdict = checks.judge("T10", control(readback={"expected": 26.0, "observed": [25.0]}))
    assert not verdict["S"]["detected"] and verdict["C"]["targeted"]


def test_release_value_zero_and_release_left_in_place():
    zero = [{"op": "release", "token": "writer", "value": 0, "reached_ri": True, "status": 400, "body": {}}]
    assert checks.judge("T11", control(requests=zero, readback=None, schema={"enum": [1]}))["C"]["targeted"]
    one = [{"op": "release", "token": "writer", "value": 1, "reached_ri": True, "status": 202, "body": {"controlId": "r"}}]
    left = {"priority_array": [None] * 7 + [24.0] + [None] * 8, "present_value": 24.0, "relinquish_default": 23.0}
    verdict = checks.judge("T12", control(requests=one, readback=None, schema={"enum": [1]}, release_after=left))
    assert not verdict["S"]["detected"] and verdict["C"]["targeted"]


def test_a_safety_refusal_makes_the_injection_not_tested():
    trace = control()
    trace["requests"] = [dict(trace["requests"][0], reached_ri=False, status=None, safety={"status": "rejected"})]
    assert checks.judge("T6", trace)["status"] == "Not Tested"


def test_the_suite_sha_is_the_preregistered_one():
    # Ported: the published suite is redacted, so its own sha differs; the original's sha (recorded at export) must match.
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    files = json.loads((root / "release/export-provenance.json").read_text())["files"]
    suite = next(f for f in files if f["dst"].endswith("bos-contract-suite.yaml"))
    assert suite["source_sha256"] == checks.SUITE_SHA256


def test_targets_cover_the_13_testbed_injections():
    assert len(checks.TARGET) == 13 and copy.copy(set(checks.TARGET.values())) == {"telemetry_read", "time", "control_write", "release"}


# test_a_recorded_lake_row_becomes_a_telemetry_reading is not ported: it exercises scripts/b3_lab/normal.py, which
# reads private run records and is not part of the public package.


def test_an_alias_read_is_flagged_by_c_whether_refused_or_answered():
    for status, rows in ((403, []), (404, []), (200, [row(point="p1")])):
        trace = {**telemetry(rows), "id_space_reads": True}
        for read in trace["reads"]:
            read.update(point_id="p1", status=status)
        verdict = checks.judge("T2a", trace)
        assert verdict["C"]["detected"] and verdict["C"]["targeted"]
        assert verdict["S"]["detected"] == (status != 200)


def test_a_registered_read_is_not_an_id_space_flag():
    assert not checks.judge("T2a", telemetry([row()]))["C"]["detected"]


def test_component_traces_do_not_judge_their_alias_reads():
    trace = telemetry([row()])
    trace["reads"].append({"api": "history", "point_id": "p1", "status": 200, "rows": []})
    assert not checks.judge("T1", trace)["C"]["detected"]
