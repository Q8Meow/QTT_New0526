from .pr161b_test_support import records, summary


def test_pr161b_canonical_alias_repair_report_is_present():
    assert "covered_by_canonical_alias_count" in summary()
    assert isinstance(records("alias_repair"), list)
