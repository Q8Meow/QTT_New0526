from tests.pr169_dash1_ui1.r1_contract_assertions import assert_no_fake_cash_or_positions


def test_ui1_no_fake_cash_or_live_positions() -> None:
    assert_no_fake_cash_or_positions()
