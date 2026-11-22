from bos_contract_testbed import lifecycle as s4

EMPTY = [None] * 16


def arr(p8=None, p16=None):
    a = list(EMPTY)
    a[7], a[15] = p8, p16
    return a


def test_expected_lifecycle_is_judged_as_expected():
    before = {"priority_array": arr(23.5, 26.0), "present_value": 23.5, "relinquish_default": 28.0}
    after = {"priority_array": arr(None, 26.0), "present_value": 26.0, "relinquish_default": 28.0}
    end = {"priority_array": arr(), "present_value": 28.0, "relinquish_default": 28.0}
    assert s4.judge(before, after, end, 26.0, 23.5) == {"E1": True, "E2": True, "E5": True}


def test_falling_back_to_the_default_despite_priority_16_fails_e2():
    after = {"priority_array": arr(None, 26.0), "present_value": 28.0, "relinquish_default": 28.0}
    assert s4.judge(None, after, None, 26.0, 23.5)["E2"] is False


def test_a_missing_or_failed_read_is_not_tested_not_false(tmp_path):
    after = {"priority_array": arr(None, 26.0), "present_value": 26.0, "relinquish_default": 28.0}
    verdict = s4.judge(None, after, None, 26.0, 23.5)
    assert verdict["E1"] is None and verdict["E5"] is None and verdict["E2"] is True
    assert s4.scenario(verdict).startswith("Not Tested")
    assert s4.scenario({**verdict, "E1": False}) == "not as expected"
    failed = tmp_path / "priority-b13-end.json"
    failed.write_text('{"status": "Fail", "error_type": "ValueError"}')
    assert s4.read_priority(failed) is None
