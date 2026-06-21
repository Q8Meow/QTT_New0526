from tools.pr168_data1_validator import run_validation


def test_pr168_data1_public_fetch_summary_exists() -> None:
    run_validation("public_fetch_summary_exists")
