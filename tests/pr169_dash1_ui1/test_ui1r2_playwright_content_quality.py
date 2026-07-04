from tests.pr169_dash1_ui1.r2_contract_assertions import assert_playwright_content_quality_contract


def test_ui1r2_playwright_content_quality() -> None:
    assert_playwright_content_quality_contract()
