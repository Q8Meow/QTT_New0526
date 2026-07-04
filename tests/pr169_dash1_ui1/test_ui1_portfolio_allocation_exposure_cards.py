from tests.pr169_dash1_ui1.r1_contract_assertions import assert_portfolio_exposure_cards


def test_ui1_portfolio_allocation_exposure_cards() -> None:
    assert_portfolio_exposure_cards()
