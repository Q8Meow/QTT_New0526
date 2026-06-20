from tools.pr168_rp_validator import run_validation


def test_artifact_information_value_dag() -> None:
    run_validation("artifact_information_value_dag")
