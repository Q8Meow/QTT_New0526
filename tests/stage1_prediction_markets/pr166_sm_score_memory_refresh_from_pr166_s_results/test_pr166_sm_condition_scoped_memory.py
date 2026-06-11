from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.enums import (
    ALLOWED_MEMORY_OUTCOMES,
)


def test_pr166_sm_memory_is_condition_scoped(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_RefreshedMemoryLedger.report.json"]
    assert len(rows) == 3985
    for row in rows[:300]:
        assert row["memory_outcome"] in ALLOWED_MEMORY_OUTCOMES
        assert row["condition_scoped_memory_only"] is True
        assert row["global_permanent_ban_created"] is False
        assert row["condition_fingerprint_id"].startswith("PR165_B_CONDITION_FINGERPRINT::")
        assert 0.0 <= row["scenario_similarity_score"] <= 1.0
        assert row["matched_condition_buckets"]
