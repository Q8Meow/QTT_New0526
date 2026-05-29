from .pr161a_test_support import records, summary


def test_pr161a_candidate_first_completion_has_no_terminal_missing_blockers():
    assert summary()["still_missing_after_all_lanes_count"] == 0
    assert summary()["generic_blocker_count"] == 0
    assert all(record["attempted_fill_lanes"] for record in records("field_inventory")[:200])

