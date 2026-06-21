from tools.pr168_data1_validator import run_validation


def test_pr168_data1_quantum_forward_coefficient_feature_surface_exists() -> None:
    run_validation("quantum_forward_coefficient_feature_surface_exists")
