from src.qtt.stage1_prediction_markets.pr168_rp5d_r1_unlock.validator import run_validation


def test_rp5d_r1_validator_accepts_generated_artifacts() -> None:
    result = run_validation()
    assert result["validation"] == "PR168_RP5D_R1_EXEC_NOW_UNLOCK_OK"
    assert result["rows_promoted"] == 5
