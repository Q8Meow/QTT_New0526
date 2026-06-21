from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_real_positive_negative_requires_formula_execution_and_provenance() -> None:
    for row in load("PR168_GFP2_RealPositiveNegativeProofLedger.report.json")[:1000]:
        assert row["real_positive_claim_allowed_flag"] is False
        assert row["real_negative_claim_allowed_flag"] is False
        assert "ACCEPTED_REAL_MARKET_DATA_ABSENT" in row["proof_block_reason_codes"]
