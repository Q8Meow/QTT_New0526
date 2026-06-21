from tools.pr168_data1_validator import run_validation


def test_pr168_data1_no_private_account_or_order_endpoints_used() -> None:
    run_validation("no_private_account_or_order_endpoints_used")
