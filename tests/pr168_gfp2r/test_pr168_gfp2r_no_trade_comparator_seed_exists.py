from tests.pr168_gfp2r._helpers import record_rows, records, rows


def test_pr168_gfp2r_no_trade_comparator_seed_exists() -> None:
    assert records("PR168_GFP2R_NoTradeComparatorSeed")["no_trade_baseline_ref"]
    assert record_rows("PR168_GFP2R_NoTradeComparatorSeed")
    assert any(row["candidate_output_classification"] == "CANDIDATE_NO_TRADE_PREFERRED_NON_PROOF" for row in rows("formula_execution"))
