from .conftest import assert_rows


def test_pr166_sf_qku_tradability_rows_cover_targets(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_QKUTradabilityLedger.report.json")
    assert len(rows) == 6502
    assert all(0 <= row["qku_tradability_readiness_score"] <= 1 for row in rows[:100])
    assert all(row["tradeability_materialized_flag"] is True for row in rows[:100])
