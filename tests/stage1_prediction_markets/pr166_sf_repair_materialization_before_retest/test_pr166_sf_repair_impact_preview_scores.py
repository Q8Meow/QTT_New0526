from .conftest import assert_rows


def test_pr166_sf_repair_preview_scores_are_computed(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairPreviewScoreRegistry.report.json")
    for row in rows[:100]:
        assert "repair_priority_score_v1" in row
        assert "retest_readiness_score_v1" in row
        assert row["positive_repair_preview_class"] != "LIVE_PROFIT_EVIDENCE"
