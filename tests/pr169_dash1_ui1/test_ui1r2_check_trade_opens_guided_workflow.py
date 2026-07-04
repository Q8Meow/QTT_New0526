from tests.pr169_dash1_ui1.r2_contract_assertions import assert_guided_flows, assert_next_step_route


def test_ui1r2_check_trade_opens_guided_workflow() -> None:
    assert_next_step_route("NEXT_STEP_CHECK_TRADE_WITH_QTT_AGENTS", "guided-workflows", "OwnerTradeCheckRequestPreviewV1")
    assert_guided_flows()
