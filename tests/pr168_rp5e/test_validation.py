from src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.validator import (
    run_validation,
)


def test_rp5e_validator_accepts_generated_artifacts() -> None:
    result = run_validation()
    assert result["validation"] == "PR168_RP5E_STACK_GENERATOR_OK"
    assert result["runtime_stack_preview_rows"] == 52
    assert result["retained_topk_preview_rows"] == 50
