from .conftest import assert_rows


def test_pr166_sf_microstructure_repair_has_fill_realism(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_MicrostructureRepairLedger.report.json")
    for row in rows[:100]:
        assert row["maker_taker_role_class"]
        assert row["depth_at_candidate_size"] >= 1
        assert 0 <= row["fill_probability_proxy"] <= 1
        assert row["latency_budget_ms"] > 0
