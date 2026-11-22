"""The published contract suite definition is structurally complete and matches the counts in its README."""
from bos_contract_testbed import suite


def test_suite_has_no_structural_problems():
    assert suite.structural_problems(suite.load()) == []


def test_suite_counts_match_the_published_table():
    # results/source-reports/contract-suite/README.md: 35 conditions = covered 21, partial 7, gap 5, conflict 2
    summary = suite.summarize(suite.load())
    assert summary["conditions"] == 35
    assert summary["by_status"] == {"covered": 21, "partial": 7, "gap": 5, "conflict": 2}
    expected = {"telemetry_read": (3, 1, 2, 1), "time": (3, 1, 2, 0), "control_write": (8, 2, 0, 1),
                "release": (4, 0, 1, 0), "authorized_query": (3, 3, 0, 0)}
    order = ("covered", "partial", "gap", "conflict")
    got = {op: tuple(by.get(s, 0) for s in order) for op, by in summary["by_operation"].items()}
    assert got == expected


def test_evidence_is_reported_as_not_tested_never_pass():
    text = suite.default_suite_text()
    report = suite.report(suite.load(), text)
    assert report["refs"] > 0
    assert report["refs_evidence"]["Pass"] == 0 and report["refs_evidence"]["Not Tested"] == report["refs"]
