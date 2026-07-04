from tests.pr169_dash1_ui1.r2_contract_assertions import assert_next_step_route


def test_ui1r2_send_to_trade_workbench_prefills_context() -> None:
    assert_next_step_route("NEXT_STEP_SEND_TO_TRADE_WORKBENCH", "trade-workbench", "OwnerTradeIntentPreviewV1")
