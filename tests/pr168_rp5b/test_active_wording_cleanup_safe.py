from tests.pr168_rp5b._helpers import final_summary, load_report, load_rows


def test_active_wording_cleanup_safe() -> None:
    report = load_report("PR168_RP5B_ActiveWordingCleanup.report.json")
    assert load_rows("active_wording_cleanup_rows") == []
    assert report["active_wording_cleanup_count"] == 0
    assert final_summary()["active_wording_cleanup_count"] == 0
