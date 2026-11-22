"""Structural check of the contract suite definition (bos-contract-suite-v0).

Ported from the private testbed (scripts/contract_suite.py at e7e020d). ``structural_problems`` and ``summarize``
are unchanged. The original also confirmed each test id against recorded run results and the RI source tree; those
records are not public, so here every test reference is reported as ``Not Tested`` (never as Pass).

    python -m bos_contract_testbed.suite [--suite PATH]
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from importlib import resources
import json
from pathlib import Path

import yaml

STATUSES = {"covered", "partial", "gap", "conflict"}
CELLS = {"Pre", "Post", "Fail", "T"}


def default_suite_text() -> str:
    return resources.files("bos_contract_testbed").joinpath("data/bos-contract-suite.yaml").read_text("utf-8")


def load(path: Path | None = None) -> dict:
    return yaml.safe_load(path.read_text("utf-8") if path else default_suite_text())


def split_ref(ref: str) -> tuple[str, str]:
    source, _, test = ref.partition(":")
    return source, test


def structural_problems(suite: dict) -> list[str]:
    """Problems with the definition itself (no records read)."""
    problems = []
    for op, body in suite["operations"].items():
        cells = {c["cell"] for c in body["conditions"]}
        if cells != CELLS:
            problems.append(f"{op}: cells {sorted(cells)} are not Pre/Post/Fail/T")
        for c in body["conditions"]:
            where = f"{op}/{c['id']}"
            if c["status"] not in STATUSES:
                problems.append(f"{where}: unknown status {c['status']!r}")
            if c["status"] in {"covered", "partial", "conflict"} and not c.get("tests"):
                problems.append(f"{where}: {c['status']} needs tests")
            if c["status"] in {"gap", "partial", "conflict"} and not c.get("gap"):
                problems.append(f"{where}: {c['status']} needs a gap text")
            if c["status"] == "gap" and c.get("tests"):
                problems.append(f"{where}: gap must not list tests (use partial)")
            for ref in c.get("tests") or []:
                if split_ref(ref)[0] not in suite["sources"]:
                    problems.append(f"{where}: unknown source in {ref!r}")
    return problems


def summarize(suite: dict) -> dict:
    by_status = Counter(c["status"] for body in suite["operations"].values() for c in body["conditions"])
    by_op = {op: dict(Counter(c["status"] for c in body["conditions"])) for op, body in suite["operations"].items()}
    return {"conditions": sum(by_status.values()), "by_status": dict(by_status), "by_operation": by_op}


def report(suite: dict, text: str) -> dict:
    refs = sorted({ref for body in suite["operations"].values() for c in body["conditions"] for ref in c.get("tests") or []})
    return {"suite_id": suite["id"], "suite_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "summary": summarize(suite), "problems": structural_problems(suite), "refs": len(refs),
            "refs_evidence": {"Pass": 0, "Fail": 0, "Skip": 0, "Not Tested": len(refs)},
            "note": "test-id evidence lives in private run records; not checked in the public package"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--suite", type=Path)
    args = parser.parse_args()
    text = args.suite.read_text("utf-8") if args.suite else default_suite_text()
    result = report(yaml.safe_load(text), text)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if not result["problems"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
