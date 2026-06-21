from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_no_unselected_orphan_pass() -> None:
    assert all(row["no_orphan_status"] for row in load("PR168_GFP2_UnselectedQKUReopenLedger.report.json")[:1000])
