"""B11: contract layers V0-V2 over the S / C predicates of :mod:`bos_contract_testbed.checks`.

Ported from the private testbed (scripts/b11_lab/layers.py at e7e020d). The layer assignment and
``judge_layers`` are unchanged. Loading the recorded B3 traces and counting the normal inputs needed private
run records and is not part of this package (see docs/reproducibility.md).

A layer is a set of condition ids, cumulative V0 ⊂ V1 ⊂ V2 (preregistration
results/source-reports/preregistration/b11-contract-layers.md §2).
"""
from __future__ import annotations

from bos_contract_testbed import checks

PREREGISTRATION = "results/source-reports/preregistration/b11-contract-layers.md"
LAYERS = ("V0", "V1", "V2")
V1 = {"pre-id-space", "pre-write-permission", "fail-out-of-range-refused", "t-invalid-release-value", "t-schema-missing"}
V2 = {"post-origin-and-quality", "post-observation-time", "fail-quality-refusable", "post-readback",
      "post-default-readback", "post-actor-result-recorded"}
LAYER_OF = {**{c: "V1" for c in V1}, **{c: "V2" for c in V2}}
# The preregistered expectation for the 13 B3 injections (§3); reported, not measured here.
EXPECTED = {"V0": ["T11", "T12", "T2a", "T6", "T7", "T9"], "V1": ["T11", "T12", "T2a", "T2b", "T6", "T7", "T9"],
            "V2": ["T10", "T11", "T12", "T2a", "T2b", "T4", "T5", "T6", "T7", "T9"]}


class UnknownCondition(RuntimeError):
    pass


def layer_of(condition: str) -> str:
    if condition not in LAYER_OF:
        raise UnknownCondition(condition)
    return LAYER_OF[condition]


def within(layer: str, at: str) -> bool:
    """A flag raised at layer `at` counts at `layer` (cumulative)."""
    return LAYERS.index(at) <= LAYERS.index(layer)


def judge_layers(injection: str, trace: dict) -> dict:
    base = checks.judge(injection, trace)
    if base["status"] != "Tested":
        return base
    s, c = base["S"]["flags"], base["C"]["flags"]
    flags = [{"layer": "V0", "condition": "S", "operation": None, "reason": r} for r in s]
    flags += [{"layer": layer_of(f["condition"]), **f} for f in c]
    out = {"injection": injection, "status": "Tested", "target": checks.TARGET[injection], "layers": {}}
    for layer in LAYERS:
        hits = [f for f in flags if within(layer, f["layer"])]
        out["layers"][layer] = {"detected": bool(hits),
                                "targeted": any(f["operation"] == checks.TARGET[injection] for f in hits),
                                "conditions": sorted({f["condition"] for f in hits})}
    out["first_layer"] = next((l for l in LAYERS if out["layers"][l]["detected"]), None)
    out["flags"] = flags
    return out
