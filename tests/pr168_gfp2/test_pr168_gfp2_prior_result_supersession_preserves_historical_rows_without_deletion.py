from tests.pr168_gfp2.pr168_gfp2_test_support import load


def test_prior_result_supersession_preserves_historical_rows_without_deletion() -> None:
    for row in load("PR168_GFP2_PriorResultSupersessionLedger.report.json")[:1000]:
        assert row["historical_record_preserved_flag"] is True
        assert row["supersedes_previous_authority_flag"] is True
