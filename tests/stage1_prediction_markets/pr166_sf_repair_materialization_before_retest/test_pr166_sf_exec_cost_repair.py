from .conftest import assert_rows


def test_pr166_sf_exec_cost_repair_uses_post_cost_terms(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_ExecCostRepairLedger.report.json")
    for row in rows[:50]:
        assert row["execution_adjusted_repair_ranking_applied_flag"] is True
        assert row["post_repair_preview_is_profit_evidence_flag"] is False
        assert "spread" in row["execution_cost_terms_materialized"]
