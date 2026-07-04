from tests.pr169_dash1_ui1.r2_contract_assertions import assert_next_step_route


def test_ui1r2_explain_no_trade_opens_panel() -> None:
    assert_next_step_route("NEXT_STEP_EXPLAIN_NO_TRADE", "no-trade-panel", "NoTradeExplanationPreviewV1")
