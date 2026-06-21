from tools.pr168_data1_validator import run_validation


def test_pr168_data1_online_endpoint_discovery_report_exists() -> None:
    run_validation("online_endpoint_discovery_report_exists")
