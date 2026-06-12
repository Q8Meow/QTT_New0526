from .conftest import assert_rows


def test_pr166_sf_marginal_utility_queue_scores_rows(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairMarginalUtilityQueue.report.json")
    assert all(0 <= row["marginal_utility_score_after_repair"] <= 1 for row in rows[:100])
    assert all(row["marginal_utility_reason"] for row in rows[:100])
