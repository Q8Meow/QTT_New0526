from tests.pr162e.helpers import records


def test_post_repair_rows_have_retest_routes():
    rows = records("PR162E_PostRepairRetestQueue.report.json")
    assert rows
    assert all(row["retest_route"] == "PR162E_To_PR166_QC_Retest.report.json" for row in rows)
