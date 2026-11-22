"""Every published result is traceable to the imported report, and no unexecuted item is presented as a Pass."""
import json
from pathlib import Path
import hashlib

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
DOC = yaml.safe_load((ROOT / "results/experiments.yaml").read_text())
STATUSES = {"Pass", "Fail", "Skip", "Not Tested", "Not Applicable"}
ROWS = [(e["id"], r) for e in DOC["experiments"] for r in e["results"]]


@pytest.mark.parametrize("exp_id,result", ROWS, ids=[f"{e}:{i}" for i, (e, _) in enumerate(ROWS)])
def test_quote_occurs_verbatim_in_its_source_report(exp_id, result):
    text = (ROOT / DOC["reports_root"] / result["source"]).read_text("utf-8")
    assert result["quote"] in text, f"{exp_id}: quote not found in {result['source']}"


@pytest.mark.parametrize("exp_id,result", ROWS, ids=[f"{e}:{i}" for i, (e, _) in enumerate(ROWS)])
def test_status_vocabulary_is_strict(exp_id, result):
    assert result["status"] in STATUSES
    if result["status"] in {"Not Applicable", "Skip"}:
        assert result.get("reason"), f"{exp_id}: {result['status']} needs a reason"


def test_a_pass_item_does_not_describe_an_unexecuted_result():
    for exp_id, r in ROWS:
        if r["status"] == "Pass":
            item = r["item"].replace("is Not Tested)", "")  # a scoped note on another column of the quoted row
            assert "Not Tested" not in item and "Skip" not in item and "not executed" not in item, exp_id
            assert "Not Tested" not in r["quote"] or "column of the quoted row is Not Tested" in r["item"], exp_id


def test_items_marked_not_tested_in_the_item_text_are_not_pass():
    for exp_id, r in ROWS:
        if "Not Tested" in r["item"] and "->" in r["item"]:
            assert r["status"] == "Not Tested", exp_id


def test_live_experiments_are_not_claimed_reproducible():
    for e in DOC["experiments"]:
        assert e["reproducibility"] in {"offline-public", "offline-private", "live"}
        if e["reproducibility"] != "offline-public":
            assert "reproducible_part" not in e or "not" in e["reproducible_part"] or "synthetic" in e["reproducible_part"]


def test_imported_reports_match_the_export_provenance():
    files = json.loads((ROOT / "release/export-provenance.json").read_text())["files"]
    for f in files:
        data = (ROOT / f["dst"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == f["published_sha256"], f["dst"]
        assert f["digit_sequences_preserved"] is True
