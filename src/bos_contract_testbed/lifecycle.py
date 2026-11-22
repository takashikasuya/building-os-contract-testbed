"""B13 scenario 4: a second writer at BACnet priority 16 survives the release of priority 8.

Ported from the private testbed (scripts/b13_lab/s4.py at e7e020d): ``judge``, ``scenario`` and ``read_priority``
(``_read`` there) are unchanged. The CLI that read a live run's artifacts and parquet telemetry is not included.

E1 before the release: priority 8 holds BDE's value, priority 16 holds the second writer's, present value = priority 8.
E2 after the release: priority 8 empty, priority 16 = the second writer's value, present value = that value (not the
   relinquish default).
E5 after the second writer's relinquish: the array is empty, present value = default.
A missing or failed read makes its expectation Not Tested (None), never False.
"""
from __future__ import annotations

import json
from pathlib import Path

TOL = 1e-6
P8, P16 = 7, 15  # 0-based indexes of priority 8 and 16
PREREG = "results/source-reports/preregistration/b13-lifecycle-s4.md"


def _load(path):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else None


def read_priority(path):
    """A priority read, or None when it is missing or failed (its expectation is then Not Tested, not False)."""
    doc = _load(path)
    return doc if doc and doc.get("status") == "Pass" and "priority_array" in doc else None


def _eq(a, b):
    return a is not None and b is not None and abs(float(a) - float(b)) <= TOL


def judge(before, after, end, p16_value, bde_last):
    """True / False per expectation; None (Not Tested) when its read is missing or failed."""
    e1 = None if not before else _eq(before["priority_array"][P8], bde_last) and _eq(before["priority_array"][P16], p16_value) \
        and _eq(before["present_value"], before["priority_array"][P8])
    e2 = None if not after else after["priority_array"][P8] is None and _eq(after["priority_array"][P16], p16_value) \
        and _eq(after["present_value"], p16_value) and not _eq(after["present_value"], after["relinquish_default"])
    e5 = None if not end else all(v is None for v in end["priority_array"]) and _eq(end["present_value"], end["relinquish_default"])
    return {"E1": e1, "E2": e2, "E5": e5}


def scenario(verdict) -> str:
    """Prereg §4: holds when E1, E2, E5 all hold; fails when any is False; otherwise Not Tested."""
    if any(v is False for v in verdict.values()):
        return "not as expected"
    return "observed as expected" if all(v is True for v in verdict.values()) else "Not Tested (a read missing or failed)"
