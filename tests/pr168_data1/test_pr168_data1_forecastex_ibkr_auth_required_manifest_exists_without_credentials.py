from tools.pr168_data1_validator import run_validation


def test_pr168_data1_forecastex_ibkr_auth_required_manifest_exists_without_credentials() -> None:
    run_validation("forecastex_ibkr_auth_required_manifest_exists_without_credentials")
