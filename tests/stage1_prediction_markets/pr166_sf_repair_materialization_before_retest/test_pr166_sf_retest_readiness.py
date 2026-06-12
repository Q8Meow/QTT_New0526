from .conftest import assert_rows


def test_pr166_sf_retest_readiness_scores_are_present(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RetestReadinessRegistry.report.json")
    assert len(rows) == 6502
    assert any(row["retest_readiness_status"].startswith("READY_FOR_PR166_S2") for row in rows)
    assert all(row["ready_state_requires_replay_paper_before_promotion"] is True for row in rows[:100])
