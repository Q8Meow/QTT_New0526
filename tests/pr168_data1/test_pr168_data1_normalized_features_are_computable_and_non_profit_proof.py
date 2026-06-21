from tools.pr168_data1_validator import run_validation


def test_pr168_data1_normalized_features_are_computable_and_non_profit_proof() -> None:
    run_validation("normalized_features_are_computable_and_non_profit_proof")
