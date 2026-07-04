from tests.pr169_dash1_ui1.r2_contract_assertions import assert_no_profit_claims


def test_ui1r2_action_confidence_labels_not_profit_claims() -> None:
    assert_no_profit_claims()
