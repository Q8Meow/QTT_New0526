from tests.pr169_dash1_ui1.r1_contract_assertions import assert_playwright_report


def test_ui1_playwright_no_network_requests() -> None:
    assert_playwright_report()
