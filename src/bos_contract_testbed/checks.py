"""B3 (#43): the two checks of docs/preregistration/b2-contract-injection.md §3.2 applied to one trace.

S (structure_only of docs/contract-suite/bos-contract-suite.yaml) sees only the northbound replies: a non-2xx status
where 2xx was expected, a 202 without a controlId, and a telemetry row whose envelope fields (deviceId, pointId,
value, datetime) are missing or mistyped.

C turns the suite v0 conditions with status covered or partial into predicates (the covered part only); gap and
conflict conditions contribute none. A predicate flags either a rejection it observes or a contract violation, so
an injection is undetected only when it slipped through silently. Each flag names its condition id and the Table 5
operation, which makes "targeted" (the injection's own operation) countable.

Trace shapes (written by the injectors, read here; no live call is made):

    telemetry: {kind, registered: [id], sent: [{point_id, timestamp, value|None, attributes, accepted}],
                reads: [{api, point_id, status, rows: [TelemetryReading]}], id_space_reads?: bool}
    control:   {kind, point_id, schema: {min, max} | {enum: [..]} | None, policy: allow|deny,
                requests: [{op: write|release, token: writer|reader|none, value, reached_ri, status, body}],
                readback: {expected, observed: [..]} | None, audit: {accepted, rows} | None,
                release_after: {priority_array, present_value, relinquish_default} | None}

A request that Safety refused (reached_ri false) makes the trace Not Tested (§3.2).
"""
from __future__ import annotations

import datetime as dt
import json
import math

SUITE_SHA256 = "ce211aa48e98ee10f70dbe4b5874cd66a7b78c3dd2eed1af9fce4602843cc17e"
VALUE_TOL = 1e-6
# Table 5 operation each testbed injection targets (§3.1).
TARGET = {"T1": "telemetry_read", "T2a": "telemetry_read", "T2b": "telemetry_read", "T3": "telemetry_read",
          "T4": "time", "T5": "time", "T6": "control_write", "T7": "control_write", "T8": "control_write",
          "T9": "control_write", "T10": "control_write", "T11": "release", "T12": "release"}
CLOCK_KEYS = ("gatewayId", "sim_clock_id", "sim_config_revision", "sim_time_quality")


def _instant(text):
    try:
        return dt.datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _data(row) -> dict:
    raw = row.get("data")
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _sim_time(data):
    try:
        value = float(data.get("sim_time_s"))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def envelope_problems(row) -> list[str]:
    """S on one TelemetryReading: the envelope's required fields, typed as the OpenAPI schema says."""
    problems = [f"{key} missing" for key in ("deviceId", "pointId", "value", "datetime") if row.get(key) is None]
    for key in ("deviceId", "pointId", "datetime", "data"):
        if row.get(key) is not None and not isinstance(row[key], str):
            problems.append(f"{key} not a string")
    if row.get("value") is not None and not isinstance(row["value"], (int, float, str, bool)):
        problems.append("value not number/string/boolean")
    return problems


def clock_problems(row) -> list[str]:
    """C post-origin-and-quality / pre-clock-reference on one row; a changed/missing poll carries no sim time."""
    data = _data(row)
    problems = [f"{key} missing" for key in CLOCK_KEYS if not data.get(key)]
    if data.get("sim_time_quality") == "stable_unfenced" and (_sim_time(data) is None or _sim_time(data) < 0):
        problems.append("stable row without a finite sim_time_s")
    return problems


def rewinds(rows) -> list[str]:
    """C fail-quality-refusable (its covered part): sim time never decreases along acquisition time, per point."""
    found, by_point = [], {}
    for row in rows:
        by_point.setdefault(row.get("pointId"), []).append(row)
    for point, items in by_point.items():
        last = None
        for row in sorted(items, key=lambda r: _instant(r.get("datetime")) or 0.0):
            sim = _sim_time(_data(row))
            if sim is None:
                continue
            if last is not None and sim < last - VALUE_TOL:
                found.append(f"{point}: sim time {sim} after {last}")
            last = sim
    return found


def s_flags(trace: dict) -> list[str]:
    flags = []
    if trace["kind"] == "telemetry":
        for read in trace["reads"]:
            if not 200 <= read["status"] < 300:
                flags.append(f"{read['api']} {read['point_id']}: status {read['status']}")
            for row in read["rows"]:
                flags += [f"{read['api']} {read['point_id']}: {p}" for p in envelope_problems(row)]
    else:
        for r in trace["requests"]:
            if not 200 <= r["status"] < 300:
                flags.append(f"{r['op']}: status {r['status']}")
            elif r["status"] == 202 and not isinstance((r.get("body") or {}).get("controlId"), str):
                flags.append(f"{r['op']}: 202 without controlId")
    return flags


def _outside(schema, value) -> bool:
    if "enum" in schema:
        return value not in schema["enum"]
    return value < schema["min"] - VALUE_TOL or value > schema["max"] + VALUE_TOL


def c_flags(trace: dict) -> list[dict]:
    flags = []

    def flag(condition, operation, reason):
        flags.append({"condition": condition, "operation": operation, "reason": reason})

    if trace["kind"] == "telemetry":
        registered = set(trace["registered"])
        for frame in trace["sent"]:
            if frame["point_id"] not in registered:
                flag("pre-id-space", "telemetry_read", f"{frame['point_id']}: unknown id {'accepted' if frame['accepted'] else 'rejected'}")
            elif not frame["accepted"]:
                flag("pre-id-space", "telemetry_read", f"{frame['point_id']}: registered id rejected")
        # T2a (added before the control-path runs, deviation 8): on an HTTP trace that asks for it (id_space_reads),
        # a read of an id outside the registered space is flagged whether RI refuses it (an observed rejection) or
        # answers it (a violation). The component traces (T1-T5) do not ask: their alias reads carry no HTTP status.
        for read in trace["reads"] if trace.get("id_space_reads") else []:
            if read["point_id"] not in registered:
                flag("pre-id-space", "telemetry_read", f"{read['api']} {read['point_id']}: unknown id, status {read['status']}")
        sent = {}
        for frame in trace["sent"]:
            if frame["accepted"]:
                sent.setdefault(frame["point_id"], set()).add(_instant(frame["timestamp"]))
        rows = [row for read in trace["reads"] for row in read["rows"]]
        for row in rows:
            times = sent.get(row.get("pointId"))
            if times and _instant(row.get("datetime")) not in times:
                flag("post-observation-time", "telemetry_read", f"{row.get('pointId')}: datetime {row.get('datetime')} is no sent timestamp")
            for problem in clock_problems(row):
                flag("post-origin-and-quality", "time", f"{row.get('pointId')}: {problem}")
        history = [row for read in trace["reads"] if read["api"] == "history" for row in read["rows"]]
        for problem in rewinds(history):
            flag("fail-quality-refusable", "time", problem)
        return flags

    schema = trace.get("schema")
    for r in trace["requests"]:
        if r["token"] != "writer":
            flag("pre-write-permission", "control_write", f"{r['op']} with {r['token']} token: status {r['status']}")
        if r["op"] == "release" and r["value"] != 1:
            flag("t-invalid-release-value", "release", f"release value {r['value']}: status {r['status']}")
        elif r["op"] == "write" and schema is not None and _outside(schema, r["value"]):
            flag("fail-out-of-range-refused", "control_write", f"value {r['value']} outside {schema}: status {r['status']}")
        elif r["op"] == "write" and schema is None and trace.get("policy") == "deny":
            flag("t-schema-missing", "control_write", f"no schema under deny: status {r['status']}")
    readback = trace.get("readback")
    if readback is not None and not any(abs(v - readback["expected"]) <= VALUE_TOL for v in readback["observed"]):
        flag("post-readback", "control_write", f"accepted {readback['expected']}, read back {readback['observed']}")
    audit = trace.get("audit")
    if audit is not None and audit["rows"] < audit["accepted"]:
        flag("post-actor-result-recorded", "control_write", f"{audit['rows']} audit rows for {audit['accepted']} accepted")
    after = trace.get("release_after")
    if after is not None and (any(v is not None for v in after["priority_array"])
                              or abs(after["present_value"] - after["relinquish_default"]) > VALUE_TOL):
        flag("post-default-readback", "release", "priority array not empty or present value is not the relinquish default")
    return flags


def judge(injection: str, trace: dict) -> dict:
    """§3.2: one verdict per condition on the same trace."""
    if trace["kind"] == "control" and not all(r["reached_ri"] for r in trace["requests"]):
        return {"injection": injection, "status": "Not Tested", "reason": "Safety refused before RI",
                "safety": [r.get("safety") for r in trace["requests"] if not r["reached_ri"]]}
    s, c = s_flags(trace), c_flags(trace)
    return {"injection": injection, "status": "Tested",
            "S": {"detected": bool(s), "flags": s},
            "C": {"detected": bool(c), "targeted": any(f["operation"] == TARGET[injection] for f in c), "flags": c}}
