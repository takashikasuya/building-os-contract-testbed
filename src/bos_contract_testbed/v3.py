"""B12: the V3 predicates of results/source-reports/preregistration/b12-v3-validation.md §2, and V0-V3 judging of one trace.

V0-V2 are scripts/b3_lab/checks.py unchanged, layered as scripts/b11_lab/layers.py. V3 adds four conditions that were
gap or conflict in suite v0. A flag is an observed refusal or a violation (B2 §3.2), as for the other layers.

Trace extensions read here (written by the B12 injectors; B3 traces lack them and get no V3 flag from them):

    telemetry: units: {point_id: unit}; sent[].missing: "null" | "NaN" | "Infinity" | "-Infinity" | None
    control:   schema_removed: [dataType | minValue | maxValue, ...]
"""
from __future__ import annotations

import math

from bos_contract_testbed import checks
from bos_contract_testbed import layers

LAYERS = ("V0", "V1", "V2", "V3")
V3 = ("post-unit", "fail-missing-not-filled", "fail-unverifiable-refused", "fail-release-failure-reported")
PLAUSIBLE = {"K": (173.15, 373.15), "degC": (-100.0, 100.0), "W": (0.0, 1e8), "W/m2": (0.0, 2000.0), "Pa": (0.0, 2e5),
             "ppm": (0.0, 1e5), "kg/s": (0.0, 1e3), "m/s": (0.0, 100.0), "%": (0.0, 100.0), "percent": (0.0, 100.0)}
TARGET = {**{f"U{i}": "telemetry_read" for i in (1, 2, 3)}, **{f"M{i}": "telemetry_read" for i in (1, 2, 3)},
          **{f"S{i}": "control_write" for i in (1, 2, 3)}, "R1": "release", "R2": "release", **checks.TARGET}


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def unit_problem(value, unit) -> str | None:
    """post-unit on one value: None when in range or when the unit has no preregistered range (Not Applicable)."""
    if unit not in PLAUSIBLE:
        return None
    number = _number(value)
    if number is None or not math.isfinite(number):
        return None  # not a reading of a number; fail-missing-not-filled's business
    low, high = PLAUSIBLE[unit]
    return None if low <= number <= high else f"{number} outside {unit} [{low}, {high}]"


def _missing(frame) -> bool:
    if frame.get("missing"):
        return True
    value = frame.get("value")
    if value is None:
        return True
    number = _number(value)
    return number is not None and not math.isfinite(number)


def v3_flags(trace: dict) -> list[dict]:
    flags = []

    def flag(condition, operation, reason):
        flags.append({"condition": condition, "operation": operation, "reason": reason})

    if trace["kind"] == "telemetry":
        units = trace.get("units") or {}
        rows = [row for read in trace["reads"] for row in read["rows"]]
        for row in rows:
            problem = unit_problem(row.get("value"), units.get(row.get("pointId")))
            if problem:
                flag("post-unit", "telemetry_read", f"{row.get('pointId')} {row.get('datetime')}: {problem}")
        for frame in trace["sent"]:
            if not _missing(frame):
                continue
            label = frame.get("missing") or "null"
            if not frame["accepted"]:
                flag("fail-missing-not-filled", "telemetry_read", f"{frame['point_id']} {label}: rejected")
                continue
            at = checks._instant(frame["timestamp"])
            same = [r for r in rows if r.get("pointId") == frame["point_id"] and checks._instant(r.get("datetime")) == at]
            if not same:
                flag("fail-missing-not-filled", "telemetry_read", f"{frame['point_id']} {label}: accepted, no row (dropped)")
            for r in same:
                number = _number(r.get("value"))
                if number is not None and math.isfinite(number):
                    flag("fail-missing-not-filled", "telemetry_read", f"{frame['point_id']} {label}: row value {number} (filled)")
        return flags

    removed = trace.get("schema_removed") or []
    for r in trace["requests"]:
        if r["op"] == "write" and r["token"] == "writer" and removed:
            verdict = "accepted" if 200 <= r["status"] < 300 else "refused"
            flag("fail-unverifiable-refused", "control_write", f"schema without {removed}: {verdict} (status {r['status']})")
        if r["op"] == "release":
            if not 200 <= r["status"] < 300:
                flag("fail-release-failure-reported", "release", f"release status {r['status']}")
            else:
                after = trace.get("release_after")
                if after is not None and (any(v is not None for v in after["priority_array"])
                                          or abs(after["present_value"] - after["relinquish_default"]) > checks.VALUE_TOL):
                    flag("fail-release-failure-reported", "release", "2xx, but the priority array is not empty or the present value is not the default")
    return flags


def judge(injection: str, trace: dict) -> dict:
    """One verdict per layer V0-V3 on the same trace (B11's counting, plus V3)."""
    if trace["kind"] == "control" and not all(r["reached_ri"] for r in trace["requests"]):
        return {"injection": injection, "status": "Not Tested", "reason": "Safety refused before RI"}
    target = TARGET[injection]
    flags = [{"layer": "V0", "condition": "S", "operation": None, "reason": r} for r in checks.s_flags(trace)]
    flags += [{"layer": layers.layer_of(f["condition"]), **f} for f in checks.c_flags(trace)]
    flags += [{"layer": "V3", **f} for f in v3_flags(trace)]
    out = {"injection": injection, "status": "Tested", "target": target, "layers": {}}
    for layer in LAYERS:
        hits = [f for f in flags if LAYERS.index(f["layer"]) <= LAYERS.index(layer)]
        out["layers"][layer] = {"detected": bool(hits), "targeted": any(f["operation"] == target for f in hits),
                                "conditions": sorted({f["condition"] for f in hits})}
    out["first_layer"] = next((l for l in LAYERS if out["layers"][l]["detected"]), None)
    out["flags"] = flags
    return out
