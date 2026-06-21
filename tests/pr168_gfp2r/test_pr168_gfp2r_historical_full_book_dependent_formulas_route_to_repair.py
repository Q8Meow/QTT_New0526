from tests.pr168_gfp2r._helpers import record_rows


def test_pr168_gfp2r_historical_full_book_dependent_formulas_route_to_repair() -> None:
    rows = record_rows("PR168_GFP2R_HistoricalFullBookDependencyRepairQueue")
    assert rows
    assert all(row["historical_full_book_required_flag"] is True for row in rows)
    assert all(row["historical_full_book_available_flag"] is False for row in rows)
    assert all("HISTORICAL_L2_ACQUISITION_REVIEW" in row["repair_route"] for row in rows)
