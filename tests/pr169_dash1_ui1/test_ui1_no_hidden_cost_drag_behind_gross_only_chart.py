from tests.pr169_dash1_ui1.r1_contract_assertions import assert_tca_waterfall


def test_ui1_no_hidden_cost_drag_behind_gross_only_chart() -> None:
    assert_tca_waterfall()
