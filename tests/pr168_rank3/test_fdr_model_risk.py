from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_fdr_model_risk_penalties_exist_for_every_stack() -> None:
    assert_rank3_valid()
    assert all(row["FDR_penalty"] > 0 for row in rows("fdr_model_risk"))
