from tests.pr168_gfp2r._helpers import final_summary, records


def test_pr168_gfp2r_does_not_assume_historical_full_book() -> None:
    consumption = records("PR168_GFP2R_DATA1AConsumptionAudit")
    assert consumption["historical_full_book_verified_public_rows"] == 0
    assert consumption["GFP2R_historical_full_book_assumption_allowed_flag"] is False
    assert final_summary()["historical_full_book_assumption_violation_count"] == 0
